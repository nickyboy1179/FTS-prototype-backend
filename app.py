import os
import time
from __init__ import app, db, socketio
from flask import render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from models.models import Event, EventCategory, Location, EventDays, Category

load_dotenv()


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# assistant = client.beta.assistants.create(
#     name="Locallink assistant",
#     instructions="You're job is to recommend local activities to people that ask you questions. You'll have access to a list of activities with their categories and the times at which they take place. You cannot make up activities. The title of the activity should never be translated, leave it in the original language. You should always ask if there is clarification needed. Also ask follow up questions to get towards a recommendations.",
#     tools=[{"type": "retrieval"}],
#     model="gpt-3.5-turbo-1106"
# )

# thread = client.beta.threads.create()
#
# message = client.beta.threads.messages.create(
#     thread_id=thread.id,
#     role="user",
#     content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
# )
#
# run = client.beta.threads.runs.create(
#     thread_id=thread.id,
#     assistant_id=assistant.id
# )
# time.sleep(20)
#
# run_status = client.beta.threads.runs.retrieve(
#     thread_id=thread.id,
#     run_id=run.id
# )
#
# if run_status.status == 'completed':
#     messages = client.beta.threads.messages.list(
#         thread_id=thread.id
#     )
#
#     for msg in messages.data:
#         role = msg.role
#         content = msg.content[0].text.value
#         print(f"{role.capitalize()}: {content}")

# def ask_assistant(text):
#     message = client.beta.threads.messages.create(
#         thread_id=thread.id,
#         role="user",
#         content="Can you help me find an activity in the neighbourhood?"
#     )
#
#     run = client.beta.threads.runs.create(
#         thread_id=thread.id,
#         assistant_id=assistant.id,
#         instructions="Address the user as 'Nicky'.",
#     )
#
#     run = client.beta.threads.runs.retrieve(
#         thread_id=thread.id,
#         run_id=run.id
#     )
#
#     messages = client.beta.threads.messages.list(
#         thread_id=thread.id
#     )
#     print(messages.data)
#     return messages.data


def ask_chatgpt(text):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": text,
            }
        ],
        model="gpt-3.5-turbo",
    )
    return chat_completion.choices[0].message.content


def transcript_audio():
    audio_file = open("uploads/recording.mp3", "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcript.text


def translate_audio():
    audio_file = open("uploads/recording.mp3", "rb")
    translate = client.audio.translations.create(
        model="whisper-1",
        file=audio_file
    )
    return translate.text


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']

    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the audio file to the server
    audio_file.save('uploads/recording.mp3')

    transcript = transcript_audio()

    socketio.emit('send_human_message', {'data': transcript})

    chat_completion = ask_chatgpt(transcript)
    socketio.emit('send_bot_message', {'data': chat_completion})

    return jsonify({'message': 'uploads uploaded successfully'})


if __name__ == '__main__':
    app.run(debug=True)
