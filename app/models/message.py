from datetime import datetime, timezone
from app.extensions import db

class Message(db.Model):

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=False)
    sender_session_id = db.Column(db.Integer, db.ForeignKey('cafe_sessions.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.Enum('text', 'system', name='message_type'), default='text')
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reports = db.relationship('Report', backref='message', lazy='dynamic')

    def soft_delete(self):

        self.is_deleted = True
        self.content = '[Bu mesaj silindi]'

    def __repr__(self):
        return f'<Message #{self.id} in Cafe#{self.cafe_id}>'

class DirectMessage(db.Model):

    __tablename__ = 'direct_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match_requests.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def mark_as_read(self):
        self.is_read = True

    def __repr__(self):
        return f'<DirectMessage #{self.id}>'

class DMClearance(db.Model):

    __tablename__ = 'dm_clearances'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cleared_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<DMClearance Match#{self.match_id} User#{self.user_id}>'
