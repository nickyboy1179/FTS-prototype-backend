const send_to_assist = document.querySelector('#send_to_assistant')
const form = document.querySelector('form')
const form_message = document.querySelector("#update_form")
const assistant_message = document.querySelector('#update_assistant')

send_to_assist.addEventListener('click', sendToAssistant)
form.addEventListener('submit', (e) => {
    e.preventDefault();
    displayUpdateMessage(form_message)
    setTimeout(() => form.submit(), 1000)
} )


function sendToAssistant() {
    fetch('/send-to-assistant', {
        method: 'GET'
    })
        .then(response => response.json())
        .then(data => {
            console.log(data)
            displayUpdateMessage(assistant_message)
        })
}


function displayUpdateMessage(div) {
    div.style.display = 'block';
}