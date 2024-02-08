const send_to_assist = document.querySelector('#send_to_assistant')

send_to_assist.addEventListener('click', sendToAssistant)

function sendToAssistant() {
    fetch('/send-to-assistant', {
        method: 'GET'
    })
        .then(response => response.json())
        .then(data => {
            console.log(data)
        })
}