from __init__ import db


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cost_of_entry = db.Column(db.Integer)
    organizers_notes = db.Column(db.String(255))
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)

    def __repr__(self):
        return f'<Event: {self.id} {self.name}'


class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(50))
    street_name = db.Column(db.String(255), nullable=False)
    house_number = db.Column(db.Integer, nullable=False)
    location_notes = db.Column(db.String(255))

    def __repr__(self):
        return f'Location: {self.id} {self.street_name} {self.house_number}'


class EventDays(db.Model):
    __tablename__ = 'event_days'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    day_of_week = db.Column(db.String(9), nullable=False)
    week_of_month = db.Column(db.Integer)

    def __repr__(self):
        return f'Location: {self.id} {self.event_id} {self.day_of_week} {self.week_of_month}'


class EventCategory(db.Model):
    __tablename__ = 'event_category'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)

    def __repr__(self):
        return f'Location: {self.category_id} {self.event_id}'


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'Location: {self.id} {self.name}'

