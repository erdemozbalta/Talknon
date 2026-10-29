from datetime import datetime, timezone, date
from app.extensions import db

class CafeStats(db.Model):

    __tablename__ = 'cafe_stats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafes.id'), nullable=False)
    stat_date = db.Column(db.Date, default=lambda: date.today(), nullable=False)
    total_sessions = db.Column(db.Integer, default=0)
    total_messages = db.Column(db.Integer, default=0)
    total_matches = db.Column(db.Integer, default=0)
    total_reports = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint('cafe_id', 'stat_date', name='uq_cafe_date'),
    )

    @classmethod
    def get_or_create_today(cls, cafe_id):

        today = date.today()
        stat = cls.query.filter_by(cafe_id=cafe_id, stat_date=today).first()
        if not stat:
            stat = cls(cafe_id=cafe_id, stat_date=today)
            db.session.add(stat)
            db.session.commit()
        return stat

    def increment_sessions(self):
        self.total_sessions += 1

    def increment_messages(self):
        self.total_messages += 1

    def increment_matches(self):
        self.total_matches += 1

    def increment_reports(self):
        self.total_reports += 1

    def __repr__(self):
        return f'<CafeStats Cafe#{self.cafe_id} {self.stat_date}>'
