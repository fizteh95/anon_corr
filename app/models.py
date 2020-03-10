from datetime import datetime
from app import db
import json


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tlg_chat_id = db.Column(db.Integer)
    tlg_msg_id = db.Column(db.Integer)
    text = db.Column(db.String(12000))
    from_claimant = db.Column(db.Boolean)
    from_user = db.Column(db.String(256))
    to_user = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    media_group_id = db.Column(db.String(256))
    _file_ids = db.Column(db.String(15000))

    def __repr__(self):
        return f'<Message {self.text}>'

    @property
    def file_ids(self):
        try:
            a = json.loads(self._file_ids)
            return a
        except Exception as e:
            print(f'db error: {e}')
            return []

    @file_ids.setter
    def file_ids(self, value):
        self._file_ids = json.dumps(value)


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_chat_id = db.Column(db.Integer)
    source_message_id = db.Column(db.Integer)
    current_message_id = db.Column(db.Integer)
    claimant = db.Column(db.String(256))

    def __repr__(self):
        return f'<Bot message {self.current_message_id}>'


class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    chat_id = db.Column(db.Integer)

    def __repr__(self):
        return f'<Name {self.text}>'


class Claimant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)

    def __repr__(self):
        return f'<Name {self.text}>'


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    chat_id = db.Column(db.Integer)

    def __repr__(self):
        return f'<Name {self.text}>'
