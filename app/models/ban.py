from datetime import datetime, timezone
from app.extensions import db

class Ban(db.Model):

    __tablename__ = 'bans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=True)
    banned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, default='')
    ban_type = db.Column(
        db.Enum('temporary', 'permanent', name='ban_type'),
        default='temporary', nullable=False
    )
    ban_until = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    banned_by_user = db.relationship('User', foreign_keys=[banned_by], backref='bans_given')

    def is_expired(self):

        if self.ban_type == 'permanent':
            return False
        if self.ban_until:
            ban_until_utc = self.ban_until.replace(tzinfo=timezone.utc) if self.ban_until.tzinfo is None else self.ban_until
            return datetime.now(timezone.utc) > ban_until_utc
        return False

    def revoke(self):

        self.is_active = False

    def __repr__(self):
        return f'<Ban User#{self.user_id} [{self.ban_type}]>'
