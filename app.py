import os, sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

connection = sqlite3.connect('data/database.db')

with open('data/schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

app = Flask(__name__)
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

    transcript = translate_audio()

    socketio.emit('send_human_message', {'data': transcript})

    chat_completion = ask_chatgpt(transcript)
    socketio.emit('send_bot_message', {'data': chat_completion})

    return jsonify({'message': 'uploads uploaded successfully'})


if __name__ == '__main__':
    app.run(debug=True)
