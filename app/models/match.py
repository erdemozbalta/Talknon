from datetime import datetime, timezone
from app.extensions import db

class MatchRequest(db.Model):

    __tablename__ = 'match_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=True)
    sender_session_id = db.Column(db.Integer, db.ForeignKey('cafe_sessions.id'), nullable=False)
    receiver_session_id = db.Column(db.Integer, db.ForeignKey('cafe_sessions.id'), nullable=False)
    status = db.Column(
        db.Enum('pending', 'accepted', 'rejected', name='match_status'),
        default='pending', nullable=False
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    responded_at = db.Column(db.DateTime, nullable=True)

    direct_messages = db.relationship('DirectMessage', backref='match', lazy='dynamic')

    def accept(self):

        self.status = 'accepted'
        self.responded_at = datetime.now(timezone.utc)

    def reject(self):

        self.status = 'rejected'
        self.responded_at = datetime.now(timezone.utc)

    def get_other_user_id(self, current_session_id):

        if self.sender_session_id == current_session_id:
            return self.receiver_session_id
        return self.sender_session_id

    def __repr__(self):
        return f'<MatchRequest #{self.id} [{self.status}]>'
