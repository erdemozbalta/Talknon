from datetime import date, timedelta
from app.extensions import db
from app.models.stats import CafeStats

def increment_stat(cafe_id, stat_type):
\
\
\
\
\
\

    stat = CafeStats.get_or_create_today(cafe_id)
    if stat_type == 'sessions':
        stat.increment_sessions()
    elif stat_type == 'messages':
        stat.increment_messages()
    elif stat_type == 'matches':
        stat.increment_matches()
    elif stat_type == 'reports':
        stat.increment_reports()
    db.session.commit()

def get_cafe_stats_range(cafe_id, days=7):

    start_date = date.today() - timedelta(days=days)
    stats = CafeStats.query.filter(
        CafeStats.cafe_id == cafe_id,
        CafeStats.stat_date >= start_date
    ).order_by(CafeStats.stat_date.asc()).all()
    return stats

def get_cafe_total_stats(cafe_id):

    from app.models.message import Message
    from app.models.session import CafeSession
    from app.models.match import MatchRequest
    from app.models.report import Report

    stats = CafeStats.query.filter_by(cafe_id=cafe_id).all()

    db_messages = Message.query.filter_by(cafe_id=cafe_id, is_deleted=False).count()
    db_sessions = CafeSession.query.filter_by(cafe_id=cafe_id).count()

    db_matches = MatchRequest.query.join(
        CafeSession, MatchRequest.sender_session_id == CafeSession.id
    ).filter(
        CafeSession.cafe_id == cafe_id,
        MatchRequest.status == 'accepted'
    ).count()

    db_reports = Report.query.filter_by(cafe_id=cafe_id).count()

    stats_messages = sum(s.total_messages for s in stats)
    stats_sessions = sum(s.total_sessions for s in stats)
    stats_matches = sum(s.total_matches for s in stats)
    stats_reports = sum(s.total_reports for s in stats)

    total_messages = max(db_messages, stats_messages)
    total_sessions = max(db_sessions, stats_sessions)
    total_matches = max(db_matches, stats_matches)
    total_reports = max(db_reports, stats_reports)

    totals = {
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'total_matches': total_matches,
        'total_reports': total_reports,
        'messages': total_messages,
        'sessions': total_sessions,
        'matches': total_matches,
        'reports': total_reports
    }
    return totals
