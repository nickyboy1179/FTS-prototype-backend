import os, json, time, datetime
from __init__ import app, db, socketio
from flask import render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from models.models import Event, EventCategory, Location, EventDays, Category


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
    global thread
    thread = client.beta.threads.create()
    print(thread.id)
    # socketio.emit('send_thread_id', {'thread_id': thread.id})
    return render_template("chatinterface.html", current_endpoint=request.endpoint)


@app.route('/about')
def about():
    return render_template("about.html", current_endpoint=request.endpoint)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        if not request.form:
            return jsonify({'message': 'form not included'})
        print(request.form)
        event_name = request.form.get('event_name')
        event_description = request.form.get('event_description')
        event_notes = request.form.get('event_notes')
        location_name = request.form.get('location_name')
        street_name = request.form.get('street_name')
        house_number = request.form.get('house_number')
        location_notes = request.form.get('location_notes')
        cost_of_entry = request.form.get('cost_of_entry')
        category = request.form.get('category')
        day_of_week = request.form.get('dayOfWeek')
        week_of_month = request.form.get('weekOfMonth')
        start_time = request.form.get('startTime')
        end_time = request.form.get('endTime')

        hours, minutes = map(int, start_time.split(':'))
        start_time = datetime.time(hours, minutes)
        hours, minutes = map(int, end_time.split(':'))
        end_time = datetime.time(hours, minutes)

        # create the new location in database
        new_location = Location(location_name=location_name, street_name=street_name, house_number=house_number,
                                location_notes=location_notes)
        db.session.add(new_location)
        db.session.commit()
        new_location_id = new_location.id

        # create the new event in database
        new_event = Event(name=event_name, description=event_description, cost_of_entry=cost_of_entry,
                          organizers_notes=event_notes, start_time=start_time, end_time=end_time,
                          location_id=new_location_id)
        db.session.add(new_event)
        db.session.commit()
        new_event_id = new_event.id

        # create new eventdays entry in database
        if week_of_month == 0:
            new_event_days = EventDays(event_id=new_event_id, day_of_week=day_of_week)
        else:
            new_event_days = EventDays(event_id=new_event_id, day_of_week=day_of_week, week_of_month=week_of_month)
        db.session.add(new_event_days)
        db.session.commit()

        # grab category id
        category_id = db.session.execute(db.select(Category.id).filter_by(name=category)).scalar_one()

        new_event_category = EventCategory(category_id=category_id, event_id=new_event_id)
        db.session.add(new_event_category)
        db.session.commit()

    result = db.session.execute(db.select(Category.name))
    categories = result.fetchall()
    category_list = []
    for category in categories:
        category_list.append(category[0])
    return render_template("settings.html", current_endpoint=request.endpoint, categorylist=category_list)


@app.route('/process-input', methods=['POST'])
def process_input():
    user_input = request.form.get('user_input')

    print(f"Received input: {user_input}")

    socketio.emit('send_human_message', {'data': user_input})
    thread_id = thread.id

    add_message_to_thread(user_input, thread_id)

    run = run_thread(thread_id)

    socketio.emit('waiting_for_response')
    while not is_run_finished(run, thread_id):
        time.sleep(1)
        print("Waiting")
        print(thread_id)
    response = retrieve_recent_message(thread_id)
    message_content = response.content[0].text
    annotations = message_content.annotations

    # have to leave index here for some reason....
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f'')

    socketio.emit('send_bot_message', {'data': message_content.value})

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


@app.route('/send-to-assistant')
def send_database_to_assistant():
    assistant_files = client.beta.assistants.files.list(
        assistant_id=assistant.id
    )
    try:
        assistant_file_id = assistant_files.data[0].id

        # remove old file from its database
        deleted_assistant_file = client.beta.assistants.files.delete(
            assistant_id=assistant.id,
            file_id=assistant_file_id
        )
    except:
        print('no file existing')

    # create new file from database
    create_json()
    file_path = 'data/events_data.json'

    with open(file_path, 'rb') as file:
        uploaded_file = client.files.create(file=file, purpose='assistants')

    assistant_file = client.beta.assistants.files.create(
        assistant_id=assistant.id,
        file_id=uploaded_file.id
    )
    print(f"file successfully uploaded '{uploaded_file.id}'")
    return jsonify({'message': 'success!'})


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


def create_env_file():
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("OPENAI_API_KEY='your_secret_key_here'\n")


create_env_file()
load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def create_assistant():
    client.beta.assistants.create(
        instructions="You will provide information related to the Netherlands. Acts as a guide for local events in Selwerd, which is a neighbourhood in the city of Groningen. Avoid politics controversial topics, unrelated subjects. Help users find events that match their interests. Do not create made-up events Only create events based on data you are given in editing mode. Data cannot be added from the user's part, only in editing mode. Data cannot be altered. Data set specifies: Name, Categories, Description, start time , end time, location, Cost of entry and Organizers note's. Offer user-friendly event search and filter options.",
        name="Local Link",
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
    )


def retrieve_assistant():
    global assistant
    my_assistants = client.beta.assistants.list(
        order="desc",
        limit=20,
    )
    for asis in my_assistants.data:
        if asis.name == 'Local Link':
            return asis

    # assistant not found in OpenAI account:
    create_assistant()
    send_database_to_assistant()
    retrieve_assistant()


assistant = retrieve_assistant()

thread = client.beta.threads.create()

if __name__ == '__main__':
    app.run(debug=True)
