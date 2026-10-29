from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager

class User(UserMixin, db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), default='')
    last_name = db.Column(db.String(100), default='')
    bio = db.Column(db.Text, default='')
    profile_photo = db.Column(db.String(500), default='')
    role = db.Column(db.Enum('admin', 'business', 'user', name='user_role'), default='user', nullable=False)
    status = db.Column(db.Enum('active', 'banned', 'suspended', name='user_status'), default='active', nullable=False)
    ban_until = db.Column(db.DateTime, nullable=True)
    language = db.Column(db.String(5), default='tr')
    is_matchable = db.Column(db.Boolean, default=True)
    phone_verified = db.Column(db.Boolean, default=False)
    nickname = db.Column(db.String(50), default='')
    last_nickname_change = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def can_change_nickname(self):

        if not self.last_nickname_change:
            return True, 0
        now = datetime.now(timezone.utc)
        last_change = self.last_nickname_change.replace(tzinfo=timezone.utc) if self.last_nickname_change.tzinfo is None else self.last_nickname_change
        delta = now - last_change
        days_passed = delta.total_seconds() / 86400.0
        if days_passed >= 7.0:
            return True, 0
        import math
        days_remaining = max(1, math.ceil(7.0 - days_passed))
        return False, days_remaining

    cafe_sessions = db.relationship('CafeSession', backref='user', lazy='dynamic')
    owned_cafes = db.relationship('Cafe', backref='owner', lazy='dynamic')
    sent_dms = db.relationship('DirectMessage', backref='sender', lazy='dynamic',
                               foreign_keys='DirectMessage.sender_id')
    bans_received = db.relationship('Ban', backref='banned_user', lazy='dynamic',
                                    foreign_keys='Ban.user_id')
    blocks_made = db.relationship('Block', backref='blocker', lazy='dynamic',
                                  foreign_keys='Block.blocker_id')
    blocks_received = db.relationship('Block', backref='blocked', lazy='dynamic',
                                      foreign_keys='Block.blocked_id')

    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)

    @property
    def display_phone(self):

        if not self.phone_number:
            return "Telefon Yok"
        if "TLK-" in self.phone_number:
            return "Anonim Kullanıcı"
        return self.phone_number

    @property
    def display_name(self):

        name = f"{self.first_name} {self.last_name}".strip()
        if name:
            return name
        return self.display_phone

    def is_admin(self):
        return self.role == 'admin'

    def is_business(self):
        return self.role == 'business'

    def is_banned(self):

        if self.status == 'banned':
            return True
        if self.status == 'suspended' and self.ban_until:
            ban_until_utc = self.ban_until.replace(tzinfo=timezone.utc) if self.ban_until.tzinfo is None else self.ban_until
            if datetime.now(timezone.utc) < ban_until_utc:
                return True
            else:
                self.status = 'active'
                self.ban_until = None
                db.session.commit()

        return False

    def is_banned_from_cafe(self, cafe_id):

        if self.is_banned():
            return True

        if not cafe_id:
            return False

        from app.models.ban import Ban
        active_ban = Ban.query.filter_by(user_id=self.id, cafe_id=cafe_id, is_active=True).first()
        if active_ban:
            if active_ban.is_expired():
                active_ban.revoke()
                db.session.commit()
                return False
            return True

        return False

    def get_cafe_ban_info(self, cafe_id=None):

        from app.models.ban import Ban
        ban = None
        if cafe_id:
            ban = Ban.query.filter_by(user_id=self.id, cafe_id=cafe_id, is_active=True).first()
        if not ban:
            ban = Ban.query.filter_by(user_id=self.id, is_active=True).filter(Ban.cafe_id.is_(None)).first()

        if not ban:
            if self.is_banned():
                return "Hesabınız platform genelinde süresiz olarak yasaklanmıştır."
            return None

        if ban.is_expired():
            ban.revoke()
            db.session.commit()
            return None

        is_permanent = (ban.ban_type == 'permanent')
        reason_str = ban.reason or 'İşletme Yöneticisi Tarafından Yasaklandı'

        if is_permanent:
            return f"Bu kafeden kalıcı olarak yasaklandınız. Yasaklama Nedeni: '{reason_str}'"
        else:
            expires_at = ban.ban_until
            remaining_str = "Süre Doldu"
            if expires_at:
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                diff = expires_at - datetime.now(timezone.utc)
                if diff.total_seconds() > 0:
                    hours = int(diff.total_seconds() // 3600)
                    mins = int((diff.total_seconds() % 3600) // 60)
                    if hours >= 24:
                        days = hours // 24
                        hrs = hours % 24
                        remaining_str = f"{days} gün {hrs} saat"
                    elif hours > 0:
                        remaining_str = f"{hours} saat {mins} dakika"
                    else:
                        remaining_str = f"{mins} dakika"
            return f"Bu kafeden geçici olarak yasaklandınız. Yasaklama Nedeni: '{reason_str}' | Kalan Ceza Süresi: {remaining_str}"

    def get_active_cafe_bans(self):

        from app.models.ban import Ban
        bans = Ban.query.filter(Ban.user_id == self.id, Ban.cafe_id.isnot(None), Ban.is_active == True).all()
        active_bans = []
        for b in bans:
            if b.is_expired():
                b.revoke()
                db.session.commit()
            else:
                active_bans.append(b)
        return active_bans

    def get_blocked_user_ids(self):

        made = [b.blocked_id for b in self.blocks_made.all()]
        received = [b.blocker_id for b in self.blocks_received.all()]
        return list(set(made + received))

    def active_session(self):

        if self.is_admin() or self.is_business():
            return None
        from app.models.session import CafeSession
        sess = CafeSession.query.filter_by(user_id=self.id, is_active=True).first()
        if sess:
            if not sess.cafe or not sess.cafe.is_active or self.is_banned_from_cafe(sess.cafe_id):
                sess.deactivate()
                db.session.commit()
                return None
        return sess

    def __repr__(self):
        return f'<User {self.phone_number}>'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
