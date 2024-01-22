from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
# from flask_migrate import Migrate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_NOTIFICATIONS'] = False

db = SQLAlchemy(app)
app.app_context().push()
# Migrate(app, db)

socketio = SocketIO(app, cors_allowed_origins=['http://127.0.0.1:5000'])
