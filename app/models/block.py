from datetime import datetime, timezone
from app.extensions import db

class Block(db.Model):

    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('blocker_id', 'blocked_id', name='uq_block_pair'),
    )

    @classmethod
    def is_blocked(cls, user1_id, user2_id):

        if not user1_id or not user2_id:
            return False
        return cls.query.filter(
            db.or_(
                db.and_(cls.blocker_id == user1_id, cls.blocked_id == user2_id),
                db.and_(cls.blocker_id == user2_id, cls.blocked_id == user1_id)
            )
        ).first() is not None

    def __repr__(self):
        return f'<Block {self.blocker_id} -> {self.blocked_id}>'
