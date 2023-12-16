import os, json
from flask import Flask
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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
audio_file = open("Testaudio.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file
)

audio_file = open("Testaudio.mp3", "rb")
translation = client.audio.translations.create(
    model="whisper-1",
    file=audio_file
)

print(transcript)
print(translation)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
