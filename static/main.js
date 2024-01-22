const mic_btn = document.querySelector('#mic');
const send_btn = document.querySelector('#send_btn')
const input_field = document.querySelector('#user_input')
let thread_id

mic_btn.addEventListener('click', ToggleMic);
send_btn.addEventListener('click', SendButtonClicked);

let can_record = false;
let is_recording = false;

let recorder = null;

let chunks = [];

const socket = io.connect('http://localhost:' + location.port);
const message_board = document.querySelector('#chat')
const human_message = document.querySelector('.user-bubble-wrapper')
const human_message_content = document.querySelector('.user-bubble')
const bot_message = document.querySelector('.assistant-bubble-wrapper')
const bot_message_content = document.querySelector('.assistant-bubble')


function SetupAudio() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia()) {
        navigator.mediaDevices
            .getUserMedia({
                audio: true
            })
            .then(SetupStream)
            .catch(err => {
                console.error(err)
        });
    }
}
SetupAudio()

function SetupStream(stream) {
    recorder = new MediaRecorder(stream);

    recorder.ondataavailable = e => {
        chunks.push(e.data);
    }

    recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/mp3; codecs=opus" })
        chunks = [];
        // playback.src =  window.URL.createObjectURL(blob);

        sendAudioToServer(blob)
    }

    can_record = true;
}

function ToggleMic() {
    // console.log(can_record)
    if (!can_record) return;

    is_recording = !is_recording;

    if (is_recording) {
        recorder.start();
        mic_btn.classList.add("is-recording")
    } else {
        recorder.stop();
        mic_btn.classList.remove("is-recording")
    }
}

function SendButtonClicked() {
    sendTextToServer(input_field.value)
    input_field.value = "";
}

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.mp3');
    formData.append('thread_id', thread_id);

    // console.log('sending audio')
    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            console.log('Server response:', data);
        })
        .catch(error => {
            console.error('Error uploading audio: ', error)
        })
}

function sendTextToServer(text) {
    const formData = new FormData();
    formData.append('user_input', text)
    console.log('sending user_input')
    fetch('/process_input', {
        method: 'POST',
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            console.log('Server response:', data)
        })
        .catch(error => {
            console.error('Error sending user input: ', error)
        })
}

function createChatBubble(sourceDiv, text, is_human) {
    if (is_human) {
       human_message_content.textContent = text; 
    } else {
        bot_message_content.textContent = text;
    }
    let copiedDiv = sourceDiv.cloneNode(true);
    copiedDiv.style.display = 'flex';
    message_board.appendChild(copiedDiv)
}

socket.on('send_bot_message', function(data) {
    console.log(data)
    createChatBubble(bot_message, data.data, false)
})

socket.on('send_human_message', function(data) {
    console.log(data)
    createChatBubble(human_message, data.data, true)
})

socket.on('send_thread_id', function(data) {
    console.log(data)
    thread_id = data.thread_id
})