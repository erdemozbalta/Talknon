from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.dm import dm_bp
from app.extensions import db
from app.models import MatchRequest, DirectMessage, CafeSession, Block, DMClearance
from app.utils.decorators import active_user_required

@dm_bp.route('/')
@login_required
def dm_list():

    raw_pending = MatchRequest.query.join(
        CafeSession, MatchRequest.receiver_session_id == CafeSession.id
    ).filter(
        MatchRequest.status == 'pending',
        CafeSession.user_id == current_user.id
    ).order_by(MatchRequest.created_at.desc()).all()

    pending_requests = []
    for req in raw_pending:
        sender_sess = req.sender_session
        if sender_sess:
            pending_requests.append({
                'id': req.id,
                'sender_nickname': sender_sess.nickname,
                'cafe_name': sender_sess.cafe.name if sender_sess.cafe else 'Kafe',
                'cafe_slug': sender_sess.cafe.qr_unique_slug if sender_sess.cafe else '',
                'created_at': req.created_at
            })

    sender_alias = db.aliased(CafeSession)
    receiver_alias = db.aliased(CafeSession)

    matches = MatchRequest.query \
        .join(sender_alias, MatchRequest.sender_session_id == sender_alias.id) \
        .join(receiver_alias, MatchRequest.receiver_session_id == receiver_alias.id) \
        .filter(
            MatchRequest.status == 'accepted',
            db.or_(
                sender_alias.user_id == current_user.id,
                receiver_alias.user_id == current_user.id
            )
        ).order_by(MatchRequest.responded_at.desc()).all()

    conversations = []
    matched_users = []
    seen_user_ids = set()
    blocked_ids = current_user.get_blocked_user_ids()

    for match in matches:
        sender_sess = match.sender_session
        receiver_sess = match.receiver_session

        if sender_sess and sender_sess.user_id == current_user.id:
            other_session = receiver_sess
        else:
            other_session = sender_sess

        if not other_session or not other_session.user or other_session.user_id == current_user.id:
            continue

        other_user = other_session.user
        if other_user.id in blocked_ids or other_user.id in seen_user_ids:
            continue

        seen_user_ids.add(other_user.id)

        all_user_match_ids = [m.id for m in matches if (
            (m.sender_session and m.sender_session.user_id == current_user.id and m.receiver_session and m.receiver_session.user_id == other_user.id) or
            (m.receiver_session and m.receiver_session.user_id == current_user.id and m.sender_session and m.sender_session.user_id == other_user.id)
        )]

        clearance = DMClearance.query.filter_by(match_id=match.id, user_id=current_user.id).first()

        dm_query = DirectMessage.query.filter(DirectMessage.match_id.in_(all_user_match_ids))
        if clearance:
            dm_query = dm_query.filter(DirectMessage.created_at > clearance.cleared_at)

        last_dm = dm_query.order_by(DirectMessage.created_at.desc()).first()

        unread_count = DirectMessage.query.filter(
            DirectMessage.match_id.in_(all_user_match_ids),
            DirectMessage.sender_id != current_user.id,
            DirectMessage.is_read == False
        ).count()

        item = {
            'match': match,
            'other_user': other_user,
            'other_nickname': other_session.nickname or 'Kullanıcı',
            'last_message': last_dm,
            'unread_count': unread_count,
        }

        if last_dm is not None:
            conversations.append(item)

        matched_users.append(item)

    return render_template('dm/list.html',
                           conversations=conversations,
                           matched_users=matched_users,
                           pending_requests=pending_requests)

@dm_bp.route('/send-request-api', methods=['POST'])
@login_required
def send_request_api():
    if current_user.is_admin() or current_user.is_business():
        return jsonify({'status': 'error', 'message': 'Yöneticiler ve işletme hesapları eşleşme isteği gönderemez.'}), 403

    data = request.get_json(silent=True) or {}
    target_session_id = data.get('target_session_id') or request.form.get('target_session_id')

    if not target_session_id:
        return jsonify({'status': 'error', 'message': 'Eksik hedef kullanıcı bilgisi.'}), 400

    try:
        target_session_id = int(target_session_id)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Geçersiz hedef oturum kimliği.'}), 400

    from flask import session
    session_id = session.get('active_session_id')
    sender_session = None
    if session_id:
        sender_session = CafeSession.query.get(session_id)
    if not sender_session:
        sender_session = CafeSession.query.filter_by(user_id=current_user.id).order_by(CafeSession.id.desc()).first()

    target_session = CafeSession.query.get(target_session_id)
    if not target_session:
        return jsonify({'status': 'error', 'message': 'Hedef kullanıcı oturumu bulunamadı.'}), 404

    if not sender_session:
        sender_session = CafeSession(user_id=current_user.id, cafe_id=target_session.cafe_id, nickname=current_user.nickname or current_user.first_name or 'Kullanıcı')
        db.session.add(sender_session)
        db.session.commit()

    target_user = target_session.user
    if not target_user:
        return jsonify({'status': 'error', 'message': 'Hedef kullanıcı bulunamadı.'}), 404

    if sender_session.id == target_session.id:
        return jsonify({'status': 'error', 'message': 'Kendi oturumunuza eşleşme isteği gönderemezsiniz.'})

    from flask import current_app
    if sender_session.user_id == target_user.id and not current_app.debug:
        return jsonify({'status': 'error', 'message': 'Kendi kendinize eşleşme isteği gönderemezsiniz.'})

    if Block.is_blocked(current_user.id, target_user.id):
        return jsonify({'status': 'error', 'message': 'Engellenmiş bir kullanıcı ile eşleşme isteği gönderilemez.'}), 403

    if not current_user.is_matchable:
        return jsonify({'status': 'error', 'message': 'Eşleşme istekleriniz kapalı olduğu için eşleşme isteği gönderemezsiniz. Ayarlar sayfasından eşleşmeyi açabilirsiniz.'})

    if not target_user.is_matchable:
        return jsonify({'status': 'error', 'message': 'Bu kullanıcı eşleşme isteklerini kapatmış.'})

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

    from datetime import datetime, timezone
    if existing:
        if existing.status == 'accepted':
            return jsonify({'status': 'error', 'message': 'Bu kullanıcı ile zaten eşleşmiş durumdasınız.'})
        elif existing.status == 'pending':
            if existing.receiver_session_id in s_ids:
                return jsonify({
                    'status': 'info',
                    'message': f'{target_session.nickname} size zaten bir eşleşme isteği gönderdi! Mesaj & İstekler sayfasından kabul edebilirsiniz.'
                })
            else:
                return jsonify({
                    'status': 'info',
                    'message': f'{target_session.nickname} kullanıcısına zaten bir eşleşme isteği gönderdiniz, yanıt bekleniyor.'
                })
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

    from app.extensions import socketio
    socketio.emit('match_request_received', notif_payload, room=f"user_{target_user.id}")

    return jsonify({
        'status': 'success',
        'message': f'{target_session.nickname} kullanıcısına eşleşme isteği gönderildi.'
    })

@dm_bp.route('/respond-request/<int:request_id>', methods=['POST'])
@login_required
def respond_request(request_id):

    match_req = MatchRequest.query.get_or_404(request_id)
    action = request.form.get('action') or (request.json.get('action') if request.is_json else None)

    receiver_user_id = match_req.receiver_session.user_id if match_req.receiver_session else None
    if receiver_user_id != current_user.id:
        if request.is_json:
            return jsonify({'status': 'error', 'message': 'Yetkisiz erişim'}), 403
        flash('Bu isteğe yanıt verme yetkiniz yok.', 'danger')
        return redirect(url_for('dm.dm_list'))

    from app.utils.helpers import get_unread_notifications_count
    from app.extensions import socketio

    if action == 'accept':
        match_req.accept()
        db.session.commit()

        receiver_uid = current_user.id
        receiver_unread = get_unread_notifications_count(receiver_uid)
        socketio.emit('unread_notifications_updated', {'unread_count': receiver_unread}, room=f"user_{receiver_uid}")

        if match_req.sender_session:
            sender_uid = match_req.sender_session.user_id
            sender_unread = get_unread_notifications_count(sender_uid)
            recv_nick = match_req.receiver_session.nickname if match_req.receiver_session else 'Kullanıcı'
            sender_user = match_req.sender_session.user if match_req.sender_session else None
            receiver_user = current_user
            partner_name_for_sender = receiver_user.display_name
            partner_name_for_receiver = sender_user.display_name if sender_user else (match_req.sender_session.nickname if match_req.sender_session else 'Kullanıcı')
            partner_photo_for_sender = receiver_user.profile_photo or ''
            partner_photo_for_receiver = sender_user.profile_photo if sender_user else ''

            socketio.emit('match_accepted', {
                'match_id': match_req.id,
                'by_nickname': recv_nick,
                'other_user_name': partner_name_for_sender,
                'other_user_photo': partner_photo_for_sender,
                'unread_count': sender_unread,
                'message': f'{recv_nick} eşleşme isteğinizi kabul etti!'
            }, room=f"user_{sender_uid}")
            socketio.emit('unread_notifications_updated', {'unread_count': sender_unread}, room=f"user_{sender_uid}")

            socketio.emit('match_accepted', {
                'match_id': match_req.id,
                'by_nickname': partner_name_for_receiver,
                'other_user_name': partner_name_for_receiver,
                'other_user_photo': partner_photo_for_receiver,
                'unread_count': receiver_unread,
                'message': 'Eşleşme isteği kabul edildi!'
            }, room=f"user_{receiver_uid}")

        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Eşleşme kabul edildi!', 'match_id': match_req.id, 'unread_count': receiver_unread})
        flash('Eşleşme isteği kabul edildi!', 'success')
        return redirect(url_for('dm.dm_list'))
    else:
        match_req.reject()
        db.session.commit()

        receiver_uid = current_user.id
        receiver_unread = get_unread_notifications_count(receiver_uid)
        socketio.emit('unread_notifications_updated', {'unread_count': receiver_unread}, room=f"user_{receiver_uid}")

        if match_req.sender_session:
            sender_uid = match_req.sender_session.user_id
            sender_unread = get_unread_notifications_count(sender_uid)
            socketio.emit('match_rejected', {
                'match_id': match_req.id,
                'unread_count': sender_unread,
                'message': 'Eşleşme isteği reddedildi.'
            }, room=f"user_{sender_uid}")
            socketio.emit('unread_notifications_updated', {'unread_count': sender_unread}, room=f"user_{sender_uid}")

        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Eşleşme isteği reddedildi.', 'unread_count': receiver_unread})
        flash('Eşleşme isteği reddedildi.', 'info')
        return redirect(url_for('dm.dm_list'))

@dm_bp.route('/<int:match_id>')
@login_required
def conversation(match_id):

    match = MatchRequest.query.get_or_404(match_id)

    user_sessions = CafeSession.query.filter_by(user_id=current_user.id).all()
    session_ids = [s.id for s in user_sessions]

    if match.sender_session_id not in session_ids and match.receiver_session_id not in session_ids:
        flash('Bu sohbete erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dm.dm_list'))

    if match.status != 'accepted':
        flash('Bu eşleşme henüz kabul edilmemiş.', 'warning')
        return redirect(url_for('dm.dm_list'))

    if match.sender_session_id in session_ids:
        other_session = CafeSession.query.get(match.receiver_session_id)
    else:
        other_session = CafeSession.query.get(match.sender_session_id)

    other_user = other_session.user if other_session else None
    if other_user and Block.is_blocked(current_user.id, other_user.id):
        flash('Bu kullanıcı ile engelleme durumu mevcut olduğu için sohbete erişilemez.', 'danger')
        return redirect(url_for('dm.dm_list'))

    clearance = DMClearance.query.filter_by(match_id=match_id, user_id=current_user.id).first()
    dm_query = DirectMessage.query.filter_by(match_id=match_id)
    if clearance:
        dm_query = dm_query.filter(DirectMessage.created_at > clearance.cleared_at)

    messages = dm_query.order_by(DirectMessage.created_at.asc()).all()

    unread = DirectMessage.query.filter(
        DirectMessage.match_id == match_id,
        DirectMessage.sender_id != current_user.id,
        DirectMessage.is_read == False
    ).all()
    for msg in unread:
        msg.mark_as_read()
    db.session.commit()

    return render_template('dm/conversation.html',
                           match=match,
                           other_user=other_user,
                           other_nickname=other_session.nickname if other_session else 'Bilinmiyor',
                           messages=messages)

@dm_bp.route('/<int:match_id>/clear', methods=['POST'])
@login_required
def clear_chat(match_id):

    match = MatchRequest.query.get_or_404(match_id)
    user_sessions = CafeSession.query.filter_by(user_id=current_user.id).all()
    session_ids = [s.id for s in user_sessions]
    if match.sender_session_id not in session_ids and match.receiver_session_id not in session_ids:
        flash('Bu sohbete erişim yetkiniz yok.', 'danger')
        return redirect(url_for('dm.dm_list'))

    clearance = DMClearance.query.filter_by(match_id=match_id, user_id=current_user.id).first()
    if not clearance:
        clearance = DMClearance(match_id=match_id, user_id=current_user.id)
        db.session.add(clearance)
    else:
        clearance.cleared_at = datetime.now(timezone.utc)

    unread = DirectMessage.query.filter(
        DirectMessage.match_id == match_id,
        DirectMessage.sender_id != current_user.id,
        DirectMessage.is_read == False
    ).all()
    for m in unread:
        m.mark_as_read()

    db.session.commit()

    flash('Mesajlar temizlendi.', 'success')
    return redirect(url_for('dm.dm_list'))

@dm_bp.route('/<int:match_id>/unmatch', methods=['POST'])
@login_required
def unmatch(match_id):

    match = MatchRequest.query.get_or_404(match_id)
    user_sessions = CafeSession.query.filter_by(user_id=current_user.id).all()
    session_ids = [s.id for s in user_sessions]
    if match.sender_session_id not in session_ids and match.receiver_session_id not in session_ids:
        flash('Bu eşleşmeyi kaldırma yetkiniz yok.', 'danger')
        return redirect(url_for('dm.dm_list'))

    other_session = match.receiver_session if match.sender_session_id in session_ids else match.sender_session
    other_user_id = other_session.user_id if other_session else None

    matches_to_remove = [match]
    if other_user_id:
        sender_alias = db.aliased(CafeSession)
        receiver_alias = db.aliased(CafeSession)
        user_matches = MatchRequest.query \
            .join(sender_alias, MatchRequest.sender_session_id == sender_alias.id) \
            .join(receiver_alias, MatchRequest.receiver_session_id == receiver_alias.id) \
            .filter(
                db.or_(
                    db.and_(sender_alias.user_id == current_user.id, receiver_alias.user_id == other_user_id),
                    db.and_(sender_alias.user_id == other_user_id, receiver_alias.user_id == current_user.id)
                )
            ).all()
        if user_matches:
            matches_to_remove = user_matches

    match_ids = [m.id for m in matches_to_remove]

    DirectMessage.query.filter(DirectMessage.match_id.in_(match_ids)).delete(synchronize_session=False)
    DMClearance.query.filter(DMClearance.match_id.in_(match_ids)).delete(synchronize_session=False)

    for m in matches_to_remove:
        db.session.delete(m)

    db.session.commit()

    if other_user_id:
        try:
            from app.extensions import socketio
            from app.utils.helpers import get_unread_notifications_count
            other_unread = get_unread_notifications_count(other_user_id)
            socketio.emit('unread_notifications_updated', {'unread_count': other_unread}, room=f"user_{other_user_id}")
            for mid in match_ids:
                socketio.emit('match_removed', {
                    'match_id': mid,
                    'match_ids': match_ids,
                    'message': 'Bir eşleşmeniz sonlandırıldı.'
                }, room=f"user_{other_user_id}")
        except Exception:
            pass

    flash('Eşleşme başarıyla kaldırıldı.', 'success')
    return redirect(url_for('dm.dm_list'))
