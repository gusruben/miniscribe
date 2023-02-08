import sys
from yt_dlp import YoutubeDL
import whisper
from revChatGPT.Official import Chatbot
import asyncio
import websockets
from time import sleep
import json
import re
from queue import Queue
from threading import Thread
import os


api_key = os.getenv("OPENAI_KEY")
temperature = 0.5  # some chatgpt parameter

download_dir = "" # current directory
transcription_dir = "transcriptions"

final_filename = None
actual_filename = None


def download_video(url, progress_func):
    extension = 'wav'
    ytdl_opts = {
        "quiet": True,
        'format': f'{extension}/bestaudio/best',
        # Extract audio using ffmpeg
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': extension,
        }],
        "no-part": True,
        "outtmpl": os.path.join(download_dir, "%(id)s.%(ext)s"),
        "progress_hooks": [progress_func]
    }

    with YoutubeDL(ytdl_opts) as ydl:
        ydl.download(url)

    while not final_filename:
        sleep(0.1)

    global actual_filename
    actual_filename = final_filename[:final_filename.rfind(
        ".") + 1] + extension


async def handle(ws):
    url = await ws.recv()
    
    print(f"Generating notes for {ws.local_address[0]} ({url})")
   
    await ws.send(json.dumps({"type": "status", "data": "Downloading video...", "percent": 0}))

    to_send = Queue()

    def progress_func(d):
        global final_filename
        if final_filename is None:
            final_filename = d.get('info_dict').get('_filename')

        if d["status"] == "finished":
            to_send.put({"type": "status", "data": "Converting to audio..."})
            to_send.put(None)
        else:
            percent = re.sub("\x1b\[.+?m", "", d["_percent_str"]).strip()[:-1]
            to_send.put({"type": "status_percent", "data": percent})

    download_thread = Thread(target=download_video, args=[url, progress_func])
    download_thread.start()

    finished = False
    while not actual_filename:
        if finished:
            sleep(0.1)
            continue

        data = to_send.get()
        if data is None:

            finished = True
            continue

        await ws.send(json.dumps(data))

    await ws.send(json.dumps({"type": "status", "data": "Loading Whisper transcription model..."}))
    model = whisper.load_model("base")

    await ws.send(json.dumps({"type": "status", "data": "Transcribing audio......"}))
    transcription_filename = os.path.join(transcription_dir, actual_filename[:actual_filename.rfind(
        ".") + 1] + ".txt")
    if os.path.exists(transcription_filename):
        with open(transcription_filename, "r") as f:
            raw = f.read()
            transcription_lang = raw[:raw.find("\n")]
            transcription = raw[raw.find("\n") + 1:]
    else:
        transcription_data = model.transcribe(
            actual_filename, verbose=False)
        print(json.dumps(transcription_data))
        transcription = transcription_data["text"]
        transcription_lang = transcription_data["language"]

        with open(transcription_filename, "w") as f:
            f.write(transcription_lang + "\n" + transcription)

    await ws.send(json.dumps({"type": "transcription", "data": transcription}))
    await ws.send(json.dumps({"type": "status", "data": "Loading ChatGPT..."}))

    prompt = "You are an AI to take notes on videos. You are given the video \
transcription, and you need to summarize it using bullet points, separated by section \
titles. Format it in markdown, and do not add a 'Summary of the video' initial header. \
You will respond in English, the transcription language is '" + transcription_lang.upper() + "'. \
Here is your first transcription:\n\n```\n" + transcription + "\n```"
    chatbot = Chatbot(api_key=api_key)

    await ws.send(json.dumps({"type": "status", "data": "Generating summary..."}))
    for chunk in chatbot.ask_stream(prompt, temperature):
        await ws.send(json.dumps({"type": "notes", "data": chunk}))
        
    await ws.send(json.dumps({"type": "status", "data": "Done!"}))
    print(f"Finished generating for {ws.local_address[0]} ({url})")


async def main():
    async with websockets.serve(handle, "0.0.0.0", 3000):
        await asyncio.Future()


if __name__ == "__main__":
    if not os.path.isdir(transcription_dir):
        os.mkdir(transcription_dir)
        
    asyncio.run(main())
