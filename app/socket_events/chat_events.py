from flask import session, request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.extensions import socketio, db
from app.models import CafeSession, Message, MatchRequest, Cafe
from app.services.spam_service import check_spam, record_message
from app.services.stats_service import increment_stat
from app.utils.helpers import sanitize_message

ONLINE_SOCKETS = {}

def get_realtime_online_count(cafe_id):

    from app.models import User
    unique_users = set()
    for sid, info in ONLINE_SOCKETS.items():
        if info.get('cafe_id') == cafe_id:
            u_id = info.get('user_id')
            if u_id:
                u = User.query.get(u_id)
                if u and not (u.is_admin() or u.is_business()):
                    unique_users.add(u_id)
    return len(unique_users)

@socketio.on('join_chat')
def handle_join(data):

    if not current_user.is_authenticated or current_user.is_banned():
        return

    cafe_slug = data.get('cafe_slug')
    cafe = Cafe.query.filter_by(qr_unique_slug=cafe_slug).first()
    if not cafe:
        return

    cafe_session = CafeSession.query.filter_by(
        user_id=current_user.id, cafe_id=cafe.id, is_active=True
    ).first()
    if not cafe_session:
        return

    room = f"cafe_{cafe.id}"
    join_room(room)
    join_room(f"user_{current_user.id}")

    ONLINE_SOCKETS[request.sid] = {
        'user_id': current_user.id,
        'cafe_id': cafe.id,
        'nickname': cafe_session.nickname,
        'cafe_slug': cafe_slug,
        'session_id': cafe_session.id
    }

    active_count = get_realtime_online_count(cafe.id)

    emit('user_joined', {
        'nickname': cafe_session.nickname,
        'active_count': active_count,
        'message': ''
    }, room=room)

    from app.services.stats_service import get_cafe_total_stats
    stats = get_cafe_total_stats(cafe.id)
    emit('cafe_stats_updated', {
        'cafe_id': cafe.id,
        'active_count': active_count,
        'total_sessions': stats.get('total_sessions', 0),
        'total_messages': stats.get('total_messages', 0),
        'total_matches': stats.get('total_matches', 0)
    }, room=room)

@socketio.on('join_monitor')
def handle_join_monitor(data):

    if not current_user.is_authenticated or not (current_user.is_business() or current_user.is_admin()):
        return
    cafe_id = data.get('cafe_id')
    if cafe_id:
        room = f"cafe_{cafe_id}"
        join_room(room)
        emit('monitor_joined', {'status': 'ok', 'cafe_id': cafe_id})

@socketio.on('send_message')
def handle_message(data):

    if not current_user.is_authenticated:
        return

    session_id = session.get('active_session_id')
    if not session_id and current_user.is_authenticated:

        active_sess = CafeSession.query.filter_by(user_id=current_user.id, is_active=True).first()
        if active_sess:
            session['active_session_id'] = active_sess.id
            session['active_cafe_id'] = active_sess.cafe_id
            session_id = active_sess.id

    if not session_id:
        emit('error', {'message': 'Aktif oturumunuz yok.'})
        return

    cafe_session = CafeSession.query.get(session_id)
    if not cafe_session or not cafe_session.is_active:
        emit('error', {'message': 'Oturumunuz sonlanmış.'})
        return

    content = sanitize_message(data.get('content', ''))
    if not content:
        return

    is_spam, remaining_sec, error_msg = check_spam(current_user.id, cafe=cafe_session.cafe, message_text=content)
    if is_spam:
        emit('spam_warning', {
            'message': error_msg,
            'timeout': remaining_sec
        })
        emit('error_notification', {
            'message': error_msg
        })
        return

    message = Message(
        cafe_id=cafe_session.cafe_id,
        sender_session_id=session_id,
        content=content,
    )
    db.session.add(message)
    db.session.commit()

    increment_stat(cafe_session.cafe_id, 'messages')

    room = f"cafe_{cafe_session.cafe_id}"
    emit('new_message', {
        'id': message.id,
        'nickname': cafe_session.nickname,
        'content': content,
        'timestamp': message.created_at.isoformat(),
        'session_id': session_id,
        'user_id': current_user.id,
        'real_name': f"{current_user.first_name} {current_user.last_name}".strip() if current_user else '',
        'phone': current_user.display_phone if current_user else ''
    }, room=room)

    from app.services.stats_service import get_cafe_total_stats
    stats = get_cafe_total_stats(cafe_session.cafe_id)
    active_count = get_realtime_online_count(cafe_session.cafe_id)
    emit('cafe_stats_updated', {
        'cafe_id': cafe_session.cafe_id,
        'active_count': active_count,
        'total_sessions': stats.get('total_sessions', 0),
        'total_messages': stats.get('total_messages', 0),
        'total_matches': stats.get('total_matches', 0)
    }, room=room)

@socketio.on('leave_chat')
def handle_leave(data):

    if not current_user.is_authenticated:
        return

    cafe_slug = data.get('cafe_slug')
    cafe = Cafe.query.filter_by(qr_unique_slug=cafe_slug).first()
    if not cafe:
        return

    cafe_session = CafeSession.query.filter_by(
        user_id=current_user.id, cafe_id=cafe.id, is_active=True
    ).first()

    room = f"cafe_{cafe.id}"

    if request.sid in ONLINE_SOCKETS:
        del ONLINE_SOCKETS[request.sid]

    if cafe_session:
        nickname = cafe_session.nickname
        cafe_session.deactivate()
        db.session.commit()

        active_count = get_realtime_online_count(cafe.id)

        emit('user_left', {
            'nickname': nickname,
            'active_count': active_count,
            'message': f'{nickname} sohbetten ayrıldı'
        }, room=room)

    leave_room(room)

@socketio.on('send_match_request')
def handle_match_request(data):

    if not current_user.is_authenticated:
        emit('error', {'message': 'Lütfen önce giriş yapın.'})
        return

    if current_user.is_admin() or current_user.is_business():
        emit('error', {'message': 'Yöneticiler ve işletme hesapları eşleşme isteği gönderemez.'})
        return

    session_id = session.get('active_session_id')
    if not session_id:
        active_sess = CafeSession.query.filter_by(user_id=current_user.id).order_by(CafeSession.id.desc()).first()
        if active_sess:
            session_id = active_sess.id
            session['active_session_id'] = active_sess.id
            session['active_cafe_id'] = active_sess.cafe_id

    target_session_id = data.get('target_session_id')

    if not session_id or not target_session_id:
        emit('error', {'message': 'Geçersiz veya eksik oturum bilgisi.'})
        return

    try:
        session_id = int(session_id)
        target_session_id = int(target_session_id)
    except (TypeError, ValueError):
        emit('error', {'message': 'Geçersiz oturum formatı.'})
        return

    sender_session = CafeSession.query.get(session_id)
    target_session = CafeSession.query.get(target_session_id)

    if not sender_session or not target_session:
        emit('error', {'message': 'Kullanıcı oturumu bulunamadı.'})
        return

    target_user = target_session.user
    if not target_user:
        emit('error', {'message': 'Kullanıcı bulunamadı.'})
        return

    target_user_active = CafeSession.query.filter_by(user_id=target_user.id, is_active=True).order_by(CafeSession.id.desc()).first()
    if target_user_active:
        target_session = target_user_active

    if sender_session.id == target_session.id:
        emit('error', {'message': 'Kendi oturumunuza eşleşme isteği gönderemezsiniz.'})
        return

    from flask import current_app
    if sender_session.user_id == target_user.id and not current_app.debug:
        emit('error', {'message': 'Kendi kendinize eşleşme isteği gönderemezsiniz.'})
        return

    from app.models import Block
    if Block.is_blocked(current_user.id, target_user.id):
        emit('error', {'message': 'Engellenmiş bir kullanıcı ile eşleşme isteği gönderilemez.'})
        return

    if not current_user.is_matchable:
        emit('error', {'message': 'Eşleşme istekleriniz kapalı olduğu için eşleşme isteği gönderemezsiniz. Ayarlar sayfasından eşleşmeyi açabilirsiniz.'})
        return

    if not target_user.is_matchable:
        emit('error', {'message': 'Bu kullanıcı eşleşme isteklerini kapatmış.'})
        return

    sender_sessions = CafeSession.query.filter_by(user_id=current_user.id).all()
    target_sessions = CafeSession.query.filter_by(user_id=target_user.id).all()
    s_ids = [s.id for s in sender_sessions]
    t_ids = [s.id for s in target_sessions]

    existing = None
    if s_ids and t_ids:
        existing = MatchRequest.query.filter(
            db.or_(
                db.and_(MatchRequest.sender_session_id.in_(s_ids), MatchRequest.receiver_session_id.in_(t_ids)),
                db.and_(MatchRequest.sender_session_id.in_(t_ids), MatchRequest.receiver_session_id.in_(s_ids))
            ),
            MatchRequest.status.in_(['pending', 'accepted'])
        ).first()

    if existing:
        if existing.status == 'accepted':
            emit('error', {'message': 'Bu kullanıcı ile zaten eşleşmiş durumdasınız.'})
            return
        elif existing.status == 'pending':
            if existing.receiver_session_id in s_ids:
                emit('error', {'message': f'{target_session.nickname} size zaten bir eşleşme isteği gönderdi! Mesaj & İstekler sayfasından kabul edebilirsiniz.'})
            else:
                emit('error', {'message': f'{target_session.nickname} kullanıcısına zaten bir eşleşme isteği gönderdiniz, yanıt bekleniyor.'})
            return
    else:

        cafe_id_val = sender_session.cafe_id or target_session.cafe_id or None
        match_req = MatchRequest(
            cafe_id=cafe_id_val,
            sender_session_id=sender_session.id,
            receiver_session_id=target_session.id,
        )
        db.session.add(match_req)
        db.session.commit()

    from app.utils.helpers import get_unread_notifications_count
    unread_count = get_unread_notifications_count(target_user.id)

    sender_cafe = sender_session.cafe
    cafe_name = sender_cafe.name if sender_cafe else 'Bilinmeyen Kafe'

    notif_payload = {
        'request_id': match_req.id,
        'from_nickname': sender_session.nickname,
        'from_session_id': sender_session.id,
        'cafe_name': cafe_name,
        'unread_count': unread_count,
        'message': f'{sender_session.nickname} size bir eşleşme isteği gönderdi!'
    }

    emit('match_request_received', notif_payload, room=f"user_{target_user.id}")

    emit('match_request_sent', {
        'request_id': match_req.id,
        'to_nickname': target_session.nickname,
        'message': f'{target_session.nickname} kullanıcısına eşleşme isteği gönderildi.'
    })

@socketio.on('respond_match_request')
def handle_match_response(data):

    if not current_user.is_authenticated:
        return

    request_id = data.get('request_id')
    accepted = data.get('accepted', False)

    match_req = MatchRequest.query.get(request_id)
    if not match_req or match_req.status != 'pending':
        return

    receiver_session = CafeSession.query.get(match_req.receiver_session_id)
    if not receiver_session or receiver_session.user_id != current_user.id:
        return

    sender_session = CafeSession.query.get(match_req.sender_session_id)

    from app.utils.helpers import get_unread_notifications_count

    if accepted:
        match_req.accept()
        db.session.commit()
        increment_stat(match_req.cafe_id, 'matches')

        sender_user = sender_session.user if sender_session else None
        receiver_user = receiver_session.user

        sender_unread = get_unread_notifications_count(sender_user.id) if sender_user else 0
        receiver_unread = get_unread_notifications_count(receiver_user.id)

        if sender_user:
            emit('match_accepted', {
                'request_id': request_id,
                'match_id': match_req.id,
                'partner_name': f'{receiver_user.first_name} {receiver_user.last_name}'.strip() or receiver_session.nickname,
                'partner_photo': receiver_user.profile_photo or '',
                'partner_nickname': receiver_session.nickname,
                'other_user_name': receiver_user.display_name,
                'other_user_photo': receiver_user.profile_photo or '',
                'unread_count': sender_unread,
                'message': f'{receiver_session.nickname} eşleşme isteğinizi kabul etti!'
            }, room=f"user_{sender_user.id}")

        emit('match_accepted', {
            'request_id': request_id,
            'match_id': match_req.id,
            'partner_name': f'{sender_user.first_name} {sender_user.last_name}'.strip() if sender_user else sender_session.nickname,
            'partner_photo': sender_user.profile_photo if sender_user else '',
            'partner_nickname': sender_session.nickname if sender_session else '',
            'other_user_name': sender_user.display_name if sender_user else (sender_session.nickname if sender_session else 'Kullanıcı'),
            'other_user_photo': sender_user.profile_photo if sender_user else '',
            'unread_count': receiver_unread,
            'message': 'Eşleşme kabul edildi!'
        }, room=f"user_{receiver_user.id}")

        emit('match_accepted', {
            'request_id': request_id,
            'match_id': match_req.id,
            'partner_name': f'{sender_user.first_name} {sender_user.last_name}'.strip() if sender_user else sender_session.nickname,
            'partner_photo': sender_user.profile_photo if sender_user else '',
            'partner_nickname': sender_session.nickname if sender_session else '',
            'unread_count': receiver_unread,
            'message': 'Eşleşme kabul edildi!'
        })
    else:
        match_req.reject()
        db.session.commit()

        receiver_unread = get_unread_notifications_count(receiver_user.id)
        if sender_session:
            sender_unread = get_unread_notifications_count(sender_session.user_id)
            emit('match_rejected', {
                'request_id': request_id,
                'unread_count': sender_unread,
                'message': 'Eşleşme isteğiniz reddedildi.'
            }, room=f"user_{sender_session.user_id}")

        emit('unread_notifications_updated', {'unread_count': receiver_unread}, room=f"user_{receiver_user.id}")

@socketio.on('report_message')
def handle_report(data):

    if not current_user.is_authenticated:
        return

    from app.models import Report

    session_id = session.get('active_session_id')
    message_id = data.get('message_id')
    reported_session_id = data.get('reported_session_id') or data.get('target_session_id')
    reason = data.get('reason_details') or data.get('reason') or ''
    category_raw = data.get('reason_category') or data.get('category') or 'other'

    if not session_id and current_user.is_authenticated:
        active_sess = CafeSession.query.filter_by(user_id=current_user.id, is_active=True).first()
        if active_sess:
            session_id = active_sess.id

    if not session_id:
        emit('error', {'message': 'Aktif oturumunuz bulunamadı.'})
        return

    cafe_session = CafeSession.query.get(session_id)
    if not cafe_session:
        emit('error', {'message': 'Oturum bilgisine ulaşılamadı.'})
        return

    target_cafe_id = cafe_session.cafe_id
    if message_id:
        msg_obj = Message.query.get(message_id)
        if msg_obj:
            target_cafe_id = msg_obj.cafe_id
            if not reported_session_id:
                reported_session_id = msg_obj.sender_session_id

    if not reported_session_id or reported_session_id == session_id:
        emit('error', {'message': 'Kendi oturumunuzu veya mesajınızı raporlayamazsınız.'})
        return

    category_map = {
        'harassment': 'harassment',
        'spam': 'spam',
        'hate_speech': 'inappropriate',
        'fake': 'inappropriate',
        'inappropriate': 'inappropriate',
        'other': 'other'
    }
    category = category_map.get(category_raw, 'other')

    try:
        report = Report(
            reporter_session_id=session_id,
            reported_session_id=reported_session_id,
            message_id=message_id,
            cafe_id=target_cafe_id,
            reason=reason.strip(),
            category=category,
            status='pending'
        )
        db.session.add(report)
        db.session.commit()

        increment_stat(target_cafe_id, 'reports')

        emit('report_submitted', {
            'message': 'Raporunuz başarıyla işletmeye iletildi.'
        })

        from app.models import Cafe
        cafe_obj = Cafe.query.get(target_cafe_id)
        pending_count = Report.query.filter_by(cafe_id=target_cafe_id, status='pending').count()

        if cafe_obj and cafe_obj.owner_id:
            socketio.emit('new_report_notification', {
                'pending_count': pending_count
            }, room=f"user_{cafe_obj.owner_id}")

        emit('new_report', {
            'report_id': report.id,
            'reporter': cafe_session.nickname,
            'message_id': message_id,
            'reason': report.reason,
            'pending_count': pending_count
        }, room=f"cafe_{target_cafe_id}")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Report creation error: {e}")
        emit('error', {'message': 'Rapor kaydedilirken bir hata oluştu.'})

@socketio.on('connect')
def handle_connect():

    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")

        if current_user.is_business():
            from app.models import Cafe
            cafe = Cafe.query.filter_by(owner_id=current_user.id).first()
            if cafe:
                join_room(f"business_{cafe.id}")

@socketio.on('disconnect')
def handle_disconnect():

    sid = request.sid
    if sid in ONLINE_SOCKETS:
        info = ONLINE_SOCKETS.pop(sid)
        cafe_id = info.get('cafe_id')
        nickname = info.get('nickname')

        if cafe_id:
            room = f"cafe_{cafe_id}"
            active_count = get_realtime_online_count(cafe_id)

            emit('user_left', {
                'nickname': nickname,
                'active_count': active_count,
                'message': ''
            }, room=room)

            from app.services.stats_service import get_cafe_total_stats
            stats = get_cafe_total_stats(cafe_id)
            emit('cafe_stats_updated', {
                'cafe_id': cafe_id,
                'active_count': active_count,
                'total_sessions': stats.get('total_sessions', 0),
                'total_messages': stats.get('total_messages', 0),
                'total_matches': stats.get('total_matches', 0)
            }, room=room)
