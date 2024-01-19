import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from openai import OpenAI
from dotenv import load_dotenv
from models.models import Event, EventCategory, Location, EventDays, Category

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
# app.config['SQLALCHEMY_TRACK_NOTIFICATIONS'] = False

db = SQLAlchemy(app)
app.app_context().push()
Migrate(app, db)

socketio = SocketIO(app, cors_allowed_origins=['http://127.0.0.1:5000'])

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# chat_completion = client.chat.completions.create(
#     messages=[
#         {
#             "role": "user",
#             "content": "What is your name?",
#         }
#     ],
#     model="gpt-3.5-turbo",
# )
#
# print(chat_completion.choices[0].message.content)
# audio_file = open("uploads/recording.mp3", "rb")
# transcript = client.audio.transcriptions.create(
#     model="whisper-1",
#     file=audio_file
# )
# #
# audio_file = open("uploads/recording.mp3", "rb")
# translation = client.audio.translations.create(
#     model="whisper-1",
#     file=audio_file
# )
#
# print(transcript.text)
# print(translation)


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
