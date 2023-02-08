const genButton = document.getElementById("generateButton");
const urlInput = document.getElementById("url");
const statusElem = document.getElementById("status");
const statusText = document.getElementById("status-text");
const statusVal = document.getElementById("status-val");
const statusProgress = document.getElementById("status-progress");

const notes = document.getElementById("notes");
const transcription = document.getElementById("transcription");

let noteData = "";

function generateNotes() {
    let url = urlInput.value;

    statusElem.style.display = "inherit";

    const ws = new WebSocket("ws://" + window.location.hostname + ":3000/");

    ws.addEventListener("open", () => {
        ws.send(url);
    });
    ws.addEventListener("message", e => {
        let data = JSON.parse(e.data);

        if (data.type == "status") {
            statusText.innerText = data.data;
            if (!data.percent) {
                statusProgress.removeAttribute("value");
                statusVal.innerText = "";
            } else {
                statusProgress.value = data.percent;
                statusVal.innerText = data.percent + "%";
            }
            console.log("Status - Value:", data.data);
        } else if (data.type == "status_percent") {
            statusProgress.value = data.data;
            statusVal.innerText = data.data + "%";
            console.log("Status - Percent:", data.data);
        } else if (data.type == "transcription") {
            console.log("Got transcription, updating page");
            transcription.innerText = data.data;
        } else if (data.type == "notes") {
            console.log("Got GPT data: " + data.data);
            noteData += data.data;

            notes.innerHTML = marked.parse(noteData.trim())
        }
    });
}

genButton.addEventListener("click", generateNotes);
