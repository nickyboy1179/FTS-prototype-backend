import os, time, datetime
from __init__ import app, db, socketio
from flask import render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from models.models import Event, EventCategory, Location, EventDays, Category
import xml.etree.cElementTree as ET

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

def retrieve_events():
    events = db.session.execute(db.select(Event))
    for event in events:
        print(event)


def create_xml():

    root = ET.Element("root")
    events = db.session.execute(db.select(Event))
    for event in events:
        evnt = ET.SubElement(root, "event")

        location = db.session.execute(db.select(Location).filter_by(id=event[0].location_id)).scalar_one()
        event_category = db.session.execute(db.select(EventCategory).filter_by(event_id=event[0].id)).all()
        event_days = db.session.execute(db.select(EventDays).filter_by(event_id=event[0].id))

        category_ids = []
        for entry in event_category:
            category_ids.append(entry[0].category_id)

        categories = db.session.execute(db.select(Category).filter(Category.id.in_(category_ids)))

        ET.SubElement(evnt, "name", name="Name").text = event[0].name
        ET.SubElement(evnt, "description", name="Description").text = event[0].description
        ET.SubElement(evnt, "start_time", name="Start time").text = event[0].start_time.strftime("%H:%M")
        ET.SubElement(evnt, "end_time", name="End time").text = event[0].end_time.strftime("%H:%M")
        if event[0].cost_of_entry is None:
            ET.SubElement(evnt, "cost_of_entry", name="Cost of entry").text = 'No costs'
        else:
            ET.SubElement(evnt, "cost_of_entry", name="Cost of entry").text = event[0].cost_of_entry
        ET.SubElement(evnt, "organizers_notes", name="Organizers notes").text = event[0].organizers_notes

        cat = ET.SubElement(evnt, "categories")
        for category in categories:
            ET.SubElement(cat, "category", name="Category").text = category[0].name

        loc = ET.SubElement(evnt, "location")
        ET.SubElement(loc, "location_name", name="Location name").text = location.location_name
        ET.SubElement(loc, "street_name", name="Street name").text = location.street_name
        ET.SubElement(loc, "house_number", name="House number").text = str(location.house_number)
        ET.SubElement(loc, "location_notes", name="Location notes").text = location.location_notes

        evntdays = ET.SubElement(evnt, "days_of_week")
        wkofmnth = ET.SubElement(evnt, "weeks_of_month")
        for entry in event_days:
            ET.SubElement(evntdays, "day_of_week", name="Day of week").text = entry[0].day_of_week
            if entry[0].week_of_month is not None:
                ET.SubElement(wkofmnth, "week_of_month", name="Week of month").text = str(entry[0].week_of_month)

    tree = ET.ElementTree(root)
    tree.write("data/event_database.xml")

create_xml()

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
