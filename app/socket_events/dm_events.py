from flask_socketio import emit, join_room
from flask_login import current_user
from app.extensions import socketio, db
from app.models import MatchRequest, DirectMessage, CafeSession, Block
from app.utils.helpers import sanitize_message

@socketio.on('join_dm')
def handle_join_dm(data):

    if not current_user.is_authenticated:
        return

    match_id = data.get('match_id')
    match = MatchRequest.query.get(match_id)
    if not match or match.status != 'accepted':
        return

    user_sessions = CafeSession.query.filter_by(user_id=current_user.id).all()
    session_ids = [s.id for s in user_sessions]
    if match.sender_session_id not in session_ids and match.receiver_session_id not in session_ids:
        return

    room = f"dm_{match_id}"
    join_room(room)

@socketio.on('send_dm')
def handle_send_dm(data):

    if not current_user.is_authenticated:
        return

    match_id = data.get('match_id')
    content = sanitize_message(data.get('content', ''))

    if not match_id or not content:
        return

    match = MatchRequest.query.get(match_id)
    if not match or match.status != 'accepted':
        emit('error', {'message': 'Geçersiz eşleşme.'})
        return

    user_sessions = CafeSession.query.filter_by(user_id=current_user.id).all()
    session_ids = [s.id for s in user_sessions]
    if match.sender_session_id not in session_ids and match.receiver_session_id not in session_ids:
        emit('error', {'message': 'Bu sohbete erişim yetkiniz yok.'})
        return

    if match.sender_session_id in session_ids:
        other_session = CafeSession.query.get(match.receiver_session_id)
    else:
        other_session = CafeSession.query.get(match.sender_session_id)

    if other_session and Block.is_blocked(current_user.id, other_session.user_id):
        emit('error', {'message': 'Bu kullanıcı ile engelleme durumu mevcut olduğu için mesaj gönderilemez.'})
        return

    dm = DirectMessage(
        match_id=match_id,
        sender_id=current_user.id,
        content=content,
    )
    db.session.add(dm)
    db.session.commit()

    time_str = dm.created_at.strftime('%H:%M')
    iso_time = dm.created_at.isoformat()

    room = f"dm_{match_id}"
    dm_payload = {
        'id': dm.id,
        'match_id': match_id,
        'sender_id': current_user.id,
        'sender_name': current_user.display_name,
        'content': content,
        'time': time_str,
        'timestamp': iso_time,
        'is_read': False
    }
    emit('new_dm', dm_payload, room=room)

    other_user_id = other_session.user_id if other_session else None
    if other_user_id:
        from app.utils.helpers import get_unread_notifications_count
        count = get_unread_notifications_count(other_user_id)

        match_unread = DirectMessage.query.filter(
            DirectMessage.match_id == match_id,
            DirectMessage.sender_id == current_user.id,
            DirectMessage.is_read == False
        ).count()

        socketio.emit('new_direct_message', {
            'unread_count': count,
            'match_unread': match_unread,
            'match_id': match_id,
            'dm_id': dm.id,
            'sender_id': current_user.id,
            'sender_name': current_user.display_name,
            'content': content,
            'time': time_str,
            'timestamp': iso_time,
            'message': f'{current_user.display_name}: {content[:30]}'
        }, room=f"user_{other_user_id}")
        socketio.emit('unread_notifications_updated', {'unread_count': count}, room=f"user_{other_user_id}")

        socketio.emit('dm_conversation_updated', {
            'match_id': match_id,
            'dm_id': dm.id,
            'sender_id': current_user.id,
            'sender_name': current_user.display_name,
            'content': content,
            'time': time_str,
            'timestamp': iso_time,
            'is_own': False,
            'unread_count': match_unread,
            'total_unread': count
        }, room=f"user_{other_user_id}")

    socketio.emit('dm_conversation_updated', {
        'match_id': match_id,
        'dm_id': dm.id,
        'sender_id': current_user.id,
        'sender_name': current_user.display_name,
        'content': content,
        'time': time_str,
        'timestamp': iso_time,
        'is_own': True,
        'unread_count': 0
    }, room=f"user_{current_user.id}")

@socketio.on('read_dm')
def handle_read_dm(data):

    if not current_user.is_authenticated:
        return

    match_id = data.get('match_id')
    if not match_id:
        return

    unread = DirectMessage.query.filter(
        DirectMessage.match_id == match_id,
        DirectMessage.sender_id != current_user.id,
        DirectMessage.is_read == False
    ).all()

    if unread:
        for msg in unread:
            msg.mark_as_read()
        db.session.commit()

    room = f"dm_{match_id}"
    emit('messages_read', {
        'match_id': match_id,
        'reader_id': current_user.id
    }, room=room)

    from app.utils.helpers import get_unread_notifications_count
    current_unread = get_unread_notifications_count(current_user.id)
    emit('unread_notifications_updated', {'unread_count': current_unread}, room=f"user_{current_user.id}")
    emit('dm_messages_read', {'match_id': match_id}, room=f"user_{current_user.id}")
