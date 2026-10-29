from datetime import datetime, timezone
from app.extensions import db

class CafeSession(db.Model):

    __tablename__ = 'cafe_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_latitude = db.Column(db.Numeric(10, 8), nullable=True)
    last_longitude = db.Column(db.Numeric(11, 8), nullable=True)
    last_location_check = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    left_at = db.Column(db.DateTime, nullable=True)

    messages = db.relationship('Message', backref='sender_session', lazy='dynamic')
    sent_match_requests = db.relationship(
        'MatchRequest', backref='sender_session', lazy='dynamic',
        foreign_keys='MatchRequest.sender_session_id'
    )
    received_match_requests = db.relationship(
        'MatchRequest', backref='receiver_session', lazy='dynamic',
        foreign_keys='MatchRequest.receiver_session_id'
    )

    def deactivate(self):

        self.is_active = False
        self.left_at = datetime.now(timezone.utc)

    def update_location(self, latitude, longitude):

        self.last_latitude = latitude
        self.last_longitude = longitude
        self.last_location_check = datetime.now(timezone.utc)

    def __repr__(self):
        return f'<CafeSession {self.nickname}@Cafe#{self.cafe_id}>'
