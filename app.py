import os, time, json
from __init__ import app, db, socketio
from flask import render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from models.models import Event, EventCategory, Location, EventDays, Category

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

assistant = client.beta.assistants.retrieve("asst_gIwlJp3ZPrZltTol8lKuS7tj")

thread = client.beta.threads.create()


def add_message_to_thread(text, thread_id):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text
    )
    return message


def run_thread(thread_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant.id
    )
    return run


def is_run_finished(run, thread_id):
    run_status = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run.id
    )
    if run_status.status == 'completed':
        return True
    else:
        return False


def retrieve_recent_message(thread_id):
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    return messages.data[0]


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

    # print(thread.id)
    # socketio.emit('send_thread_id', {'thread_id': thread.id})
    return render_template("chatinterface.html")


@app.route('/process_input', methods=['POST'])
def process_input():
    user_input = request.form.get('user_input')

    print(f"Received input: {user_input}")

    socketio.emit('send_human_message', {'data': user_input})
    thread_id = thread.id

    message = add_message_to_thread(user_input, thread_id)

    run = run_thread(thread_id)

    while not is_run_finished(run, thread_id):
        time.sleep(1)
        print("Waiting")
        print(thread_id)

    response = retrieve_recent_message(thread_id)

    socketio.emit('send_bot_message', {'data': response.content[0].text.value})

    return jsonify({"message": "input successfully handled"})


@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']

    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    audio_file.save('uploads/recording.mp3')

    transcript = transcript_audio()

    socketio.emit('receive_audio_transcript', {'data': transcript})

    return jsonify({'message': 'uploads uploaded successfully'})


def create_json():
    events_data = []
    events = db.session.execute(db.select(Event))

    for event in events:
        location = db.session.execute(db.select(Location).filter_by(id=event[0].location_id)).scalar_one()
        event_category = db.session.execute(db.select(EventCategory).filter_by(event_id=event[0].id)).all()
        event_days = db.session.execute(db.select(EventDays).filter_by(event_id=event[0].id))

        category_ids = [entry[0].category_id for entry in event_category]
        categories = db.session.execute(db.select(Category).filter(Category.id.in_(category_ids)))

        event_data = {
            "name": event[0].name,
            "description": event[0].description,
            "start_time": event[0].start_time.strftime("%H:%M"),
            "end_time": event[0].end_time.strftime("%H:%M"),
            "cost_of_entry": 'No costs' if event[0].cost_of_entry is None else event[0].cost_of_entry,
            "organizers_notes": event[0].organizers_notes,
            "categories": [{"name": category[0].name} for category in categories],
            "location": {
                "location_name": location.location_name,
                "street_name": location.street_name,
                "house_number": str(location.house_number),
                "location_notes": location.location_notes
            },
            "days_of_week": [{"day_of_week": entry[0].day_of_week} for entry in event_days],
            "weeks_of_month": [str(entry[0].week_of_month) for entry in event_days if
                               entry[0].week_of_month is not None]
        }

        events_data.append(event_data)

    with open('data/events_data.json', 'w') as json_file:
        json.dump(events_data, json_file, indent=2)


if __name__ == '__main__':
    app.run(debug=True)
