import sys
from yt_dlp import YoutubeDL
import whisper
from revChatGPT.Official import Chatbot
import re
import os

api_key = os.getenv("OPENAI_KEY")
url = sys.argv[1] if len(sys.argv) > 1 else "http://0.0.0.0:8000/try-something-new-for-30-days-matt-cutts.mp4"
temperature = 0.5 # some chatgpt parameter, no idea what it means


final_filename = None
def yt_dlp_monitor(d):
    # print("\n" + re.sub("\x1b\[.+?m", "", d["_percent_str"]).strip())
    global final_filename
    if final_filename is None:
        final_filename = d.get('info_dict').get('_filename')
        
    if d["status"] == "finished":
        pass


extension = 'wav'
ytdl_opts = {
    'format': f'{extension}/bestaudio/best',
    # Extract audio using ffmpeg
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': extension,
    }],
    "no-part": True,
    "outtmpl": "%(id)s.%(ext)s",
    "progress_hooks": [yt_dlp_monitor]
}

def download_video(url):
    with YoutubeDL(ytdl_opts) as ydl:
        ydl.download(url)
        
    actual_filename = final_filename[:final_filename.rfind(".") + 1] + extension
    return actual_filename

filename = download_video(url)
# exit()
if os.path.exists("transcription.txt"):
    print("A transcription exists already, do you want to use it?")
    ans = input("(y/n) ")
    if ans.casefold().strip()[0] == "y":
        with open("transcription.txt", "r") as f:
            transcription = f.read()
    else:
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("Transcribing audio...")
        transcription = model.transcribe(filename, verbose=False)["text"]
        with open("transcription.txt", "a") as f:
            f.write(transcription)

prompt = "You are an AI to take notes on videos. You are given the video \
transcription, and you need to summarize it using bullet points, separated by section \
titles. Here is your first transcription:\n\n```\n" + transcription + "\n```"
# print(prompt)
# prompt = """You are an AI to take notes on videos. You are given the video transcription, and you need to summarize it using bullet points with section titles. Here is your first transcription:

# ```
#  A few years ago, I felt like I was stuck in a rut. So I decided to follow in the footsteps of the great American philosopher, Morgan Spurlock, and try something new for 30 days. The idea is actually pretty simple. Think about something you've always wanted to add to your life and try it for the next 30 days. It turns out, 30 days is just about the right amount of time to add a new habit or subtract a habit, like watching the news from your life. There's a few things that I learned while doing these 30 day challenges. The first was, instead of the months flying by, forgotten, the time was much more memorable. This was part of a challenge I did to take a picture every day for a month. I remember exactly where I was and what I was doing that day. I also noticed that as I started to do more and harder 30 day challenges, myself confidence grew. I went from desk dwelling computer nerd to the kind of guy who bikes to work for fun. Even last year, I ended up hiking up Mount Kilimanjaro, the highest mountain in Africa. I would never have been that adventurous before I started my 30 day challenges. I also figured out that if you really want something badly enough, you can do anything for 30 days. Have you ever wanted to write a novel? Every November, tens of thousands of people try to write their own 50,000 word novel from scratch in 30 days. It turns out all you have to do is write 1,667 words a day for a month. So I did. By the way, the secret is not to go to sleep until you've written your words for the day. You might be sleep deprived, but you'll finish your novel. Now, is my book the next great American novel? No, I wrote it in a month. It's awful. But for the rest of my life, if I meet John Hodgman at a Ted Party, I don't have to say, I'm a computer scientist. No, no. If I want to, I can say, I'm a novelist. So here's one last thing I'd like to mention. I learned that when I made small, sustainable changes, things I could keep doing, they were more likely to stick. There's nothing wrong with big, crazy challenges. In fact, there are a ton of fun, but they're less likely to stick. When I gave up sugar for 30 days, day 31 looked like this. So here's my question to you. What are you waiting for? I guarantee you the next 30 days are going to pass whether you like it or not. So why not think about something you have always wanted to try and give it a shot for the next 30 days. Thanks.
# ```"""

print("Loading ChatGPT...")
chatbot = Chatbot(api_key=api_key)

print("Generating notes...")
for chunk in chatbot.ask_stream(prompt, temperature):
    print(chunk, end="")
    sys.stdout.flush()
# print("Here are the notes on your video:")
# print(resp["choices"][0]["text"])

while True:
    q = input("\nEnter any additional questions:\n")
    print("\nChatGPT:\n")
    for chunk in chatbot.ask_stream(q, temperature):
        print(chunk, end="")
        sys.stdout.flush()
    print("\n\n")

# for chunk in chatbot.ask_stream(prompt, temperature):
#     print(chunk, end="")
#     sys.stdout.flush()