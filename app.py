from flask import Flask
from openai import OpenAI

app = Flask(__name__)

client =


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/test')
def test_api():
    return None;


if __name__ == '__main__':
    app.run()
