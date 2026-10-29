from datetime import datetime, timezone
from app.extensions import db

class Report(db.Model):

    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reporter_session_id = db.Column(db.Integer, db.ForeignKey('cafe_sessions.id'), nullable=False)
    reported_session_id = db.Column(db.Integer, db.ForeignKey('cafe_sessions.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=False)
    reason = db.Column(db.Text, default='')
    category = db.Column(
        db.Enum('inappropriate', 'harassment', 'spam', 'other', name='report_category'),
        default='other', nullable=False
    )
    status = db.Column(
        db.Enum('pending', 'reviewed', 'dismissed', name='report_status'),
        default='pending', nullable=False
    )
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime, nullable=True)

    reporter_session = db.relationship('CafeSession', foreign_keys=[reporter_session_id], backref='reports_made')
    reported_session = db.relationship('CafeSession', foreign_keys=[reported_session_id], backref='reports_against')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_reports')

    def review(self, reviewer_id, dismiss=False):

        self.status = 'dismissed' if dismiss else 'reviewed'
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f'<Report #{self.id} [{self.status}]>'
