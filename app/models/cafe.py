import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class Cafe(db.Model):

    __tablename__ = 'cafes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, default='')
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    radius_meters = db.Column(db.Integer, default=25)
    qr_code_path = db.Column(db.String(500), default='')
    qr_unique_slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, default='')
    message_cleanup_period = db.Column(
        db.Enum('never', 'daily', 'weekly', name='cleanup_period'),
        default='never', nullable=False
    )

    spam_enabled = db.Column(db.Boolean, default=True)
    spam_max_interval_ms = db.Column(db.Integer, default=500)
    spam_max_count = db.Column(db.Integer, default=5)
    spam_mute_duration = db.Column(db.Integer, default=30)

    business_code = db.Column(db.String(50), unique=True, nullable=True, index=True)
    business_password_hash = db.Column(db.String(256), nullable=True)
    business_password_plain = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    sessions = db.relationship('CafeSession', backref='cafe', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='cafe', lazy='dynamic', cascade='all, delete-orphan')
    bans = db.relationship('Ban', backref='cafe', lazy='dynamic', cascade='all, delete-orphan')
    stats = db.relationship('CafeStats', backref='cafe', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def generate_slug():

        return uuid.uuid4().hex[:12]

    def set_business_password(self, password):

        self.business_password_plain = password
        self.business_password_hash = generate_password_hash(password)

    def check_business_password(self, password):

        if not self.business_password_hash:
            return False
        return check_password_hash(self.business_password_hash, password)

    def get_active_sessions(self):

        sessions = self.sessions.filter_by(is_active=True).all()
        seen_user_ids = set()
        unique_sessions = []
        for s in sessions:
            if s.user_id not in seen_user_ids:
                seen_user_ids.add(s.user_id)
                if s.user and not (s.user.is_admin() or s.user.is_business()):
                    unique_sessions.append(s)
        return unique_sessions

    def get_active_user_count(self):

        try:
            from app.socket_events.chat_events import get_realtime_online_count
            rt_count = get_realtime_online_count(self.id)
            if rt_count > 0:
                return rt_count
        except Exception:
            pass
        return len(self.get_active_sessions())

    def clean_expired_messages(self):

        if not self.message_cleanup_period or self.message_cleanup_period == 'never':
            return 0

        now = datetime.now(timezone.utc)
        from datetime import timedelta
        from app.models.message import Message

        if self.message_cleanup_period == 'daily':
            cutoff = now - timedelta(days=1)
        elif self.message_cleanup_period == 'weekly':
            cutoff = now - timedelta(weeks=1)
        else:
            return 0

        deleted_count = Message.query.filter(
            Message.cafe_id == self.id,
            Message.created_at < cutoff
        ).delete(synchronize_session=False)
        db.session.commit()
        return deleted_count

    def __repr__(self):
        return f'<Cafe {self.name}>'
