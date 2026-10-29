from flask import render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.blueprints.chat import chat_bp
from app.extensions import db
from app.models import Cafe, CafeSession, Message, Ban
from app.services.location_service import verify_user_location
from app.services.stats_service import increment_stat
from app.utils.helpers import generate_nickname
from app.utils.decorators import active_user_required

from datetime import datetime, timezone

def get_or_reactivate_today_session(user_id, cafe_id=None):
\
\
\
\

    active = CafeSession.query.filter_by(user_id=user_id, is_active=True).first()
    if active:
        return active

    if cafe_id:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_session = CafeSession.query.filter(
            CafeSession.user_id == user_id,
            CafeSession.cafe_id == cafe_id,
            CafeSession.joined_at >= today_start
        ).order_by(CafeSession.joined_at.desc()).first()

        if today_session:
            today_session.is_active = True
            today_session.left_at = None
            db.session.commit()
            return today_session

    return None

@chat_bp.route('/')
@login_required
@active_user_required
def index():

    if not current_user.is_admin() and not current_user.is_business():
        active_session = current_user.active_session()
        if active_session and active_session.is_active:
            return redirect(url_for('chat.room', slug=active_session.cafe.qr_unique_slug))

    cafes = Cafe.query.filter_by(is_active=True).all()
    dev_mode = current_app.config.get('DEV_SKIP_LOCATION', True)

    return render_template('chat/index.html', cafes=cafes, active_session=None, dev_mode=dev_mode)

@chat_bp.route('/cafe/<slug>')
@login_required
@active_user_required
def lobby(slug):

    cafe = Cafe.query.filter_by(qr_unique_slug=slug).first()
    if not cafe:
        flash('Geçersiz veya bulunamayan kafe QR kodu / bağlantısı.', 'danger')
        return redirect(url_for('chat.index'))

    if current_user.is_banned_from_cafe(cafe.id):
        ban_msg = current_user.get_cafe_ban_info(cafe.id) or 'Bu kafenin sohbetinden yasaklandınız.'
        flash(ban_msg, 'danger')
        return redirect(url_for('chat.index'))

    if not cafe.is_active:
        flash('Bu kafe işletmesi şu anda yayında değildir.', 'warning')
        return redirect(url_for('chat.index'))

    active_session = current_user.active_session()
    if active_session and active_session.cafe_id != cafe.id and active_session.is_active:
        flash(f'Zaten "{active_session.cafe.name}" kafesinde aktif sohbetiniz bulunuyor. Başka bir kafeye katılmak için önce mevcut sohbetinizden ayrılmalısınız.', 'warning')
        return redirect(url_for('chat.room', slug=active_session.cafe.qr_unique_slug))

    existing_session = get_or_reactivate_today_session(current_user.id, cafe.id)
    if not existing_session:
        nickname = current_user.nickname or generate_nickname()
        existing_session = CafeSession(
            user_id=current_user.id,
            cafe_id=cafe.id,
            nickname=nickname
        )
        db.session.add(existing_session)
        db.session.commit()
        increment_stat(cafe.id, 'sessions')

    session['active_session_id'] = existing_session.id
    session['active_cafe_id'] = existing_session.cafe_id

    return redirect(url_for('chat.room', slug=cafe.qr_unique_slug))

@chat_bp.route('/cafe/<slug>/join', methods=['POST'])
@login_required
@active_user_required
def join_cafe(slug):

    cafe = Cafe.query.filter_by(qr_unique_slug=slug).first()
    if not cafe:
        flash('Geçersiz veya bulunamayan kafe QR kodu / bağlantısı.', 'danger')
        return redirect(url_for('chat.index'))

    if current_user.is_banned_from_cafe(cafe.id):
        ban_msg = current_user.get_cafe_ban_info(cafe.id) or 'Bu kafenin sohbetinden yasaklandınız.'
        flash(ban_msg, 'danger')
        return redirect(url_for('chat.index'))

    if not cafe.is_active:
        flash('Bu kafe işletmesi şu anda yayında değildir.', 'warning')
        return redirect(url_for('chat.index'))

    active_session = current_user.active_session()
    if active_session and active_session.cafe_id != cafe.id and active_session.is_active:
        flash(f'Zaten "{active_session.cafe.name}" kafesinde aktif sohbetiniz bulunuyor. Başka bir kafeye katılmak için önce mevcut sohbetinizden ayrılmalısınız.', 'warning')
        return redirect(url_for('chat.room', slug=active_session.cafe.qr_unique_slug))

    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)

    existing_session = get_or_reactivate_today_session(current_user.id, cafe.id)
    if existing_session:
        session['active_session_id'] = existing_session.id
        session['active_cafe_id'] = existing_session.cafe_id
        if latitude is not None and longitude is not None:
            existing_session.update_location(latitude, longitude)
            db.session.commit()
        return redirect(url_for('chat.room', slug=existing_session.cafe.qr_unique_slug))

    nickname = current_user.nickname or request.form.get('nickname', '').strip()
    if not nickname:
        nickname = generate_nickname()
        current_user.nickname = nickname
        db.session.commit()
    elif len(nickname) < 2 or len(nickname) > 30:
        flash('Takma ad 2-30 karakter arasında olmalıdır.', 'danger')
        return redirect(url_for('chat.lobby', slug=slug))

    skip_location = current_app.config.get('DEV_SKIP_LOCATION', False)
    if not skip_location:
        if latitude is not None and longitude is not None:
            is_valid, distance, _ = verify_user_location(latitude, longitude, cafe.id)
            if not is_valid:
                flash(f'Konumunuz kafenin kapsama alani disinda ({distance}m uzakta).', 'danger')
                return redirect(url_for('chat.lobby', slug=slug))

    cafe_session = CafeSession(
        user_id=current_user.id,
        cafe_id=cafe.id,
        nickname=nickname,
        last_latitude=latitude,
        last_longitude=longitude,
    )
    db.session.add(cafe_session)
    db.session.commit()

    increment_stat(cafe.id, 'sessions')

    session['active_session_id'] = cafe_session.id
    session['active_cafe_id'] = cafe.id

    return redirect(url_for('chat.room', slug=slug))

@chat_bp.route('/cafe/<slug>/chat')
@login_required
@active_user_required
def room(slug):

    cafe = Cafe.query.filter_by(qr_unique_slug=slug).first()
    if not cafe:
        active_sess = current_user.active_session()
        if active_sess:
            active_sess.deactivate()
            db.session.commit()
        session.pop('active_session_id', None)
        session.pop('active_cafe_id', None)
        flash('Geçersiz veya bulunamayan kafe QR kodu / bağlantısı.', 'danger')
        return redirect(url_for('chat.index'))

    if current_user.is_banned_from_cafe(cafe.id):
        active_sess = current_user.active_session()
        if active_sess:
            active_sess.deactivate()
            db.session.commit()
        session.pop('active_session_id', None)
        session.pop('active_cafe_id', None)
        ban_msg = current_user.get_cafe_ban_info(cafe.id) or 'Bu kafenin sohbetinden yasaklandınız.'
        flash(ban_msg, 'danger')
        return redirect(url_for('chat.index'))

    if not cafe.is_active:
        active_sess = current_user.active_session()
        if active_sess:
            active_sess.deactivate()
            db.session.commit()
        session.pop('active_session_id', None)
        session.pop('active_cafe_id', None)
        flash('Katıldığınız kafe işletmesi veya yönetici tarafından yayından kaldırıldığı için sohbet sonlandırıldı.', 'warning')
        return redirect(url_for('chat.index'))

    if current_user.is_banned_from_cafe(cafe.id):
        ban_msg = current_user.get_cafe_ban_info(cafe.id) or 'Bu kafenin sohbetinden yasaklandınız.'
        flash(ban_msg, 'danger')
        return redirect(url_for('chat.index'))

    active_session = current_user.active_session()
    if active_session and active_session.cafe_id != cafe.id and active_session.is_active:
        flash(f'Zaten "{active_session.cafe.name}" kafesinde aktif sohbetiniz bulunuyor. Başka bir kafeye katılmak için önce mevcut sohbetinizden ayrılmalısınız.', 'warning')
        return redirect(url_for('chat.room', slug=active_session.cafe.qr_unique_slug))

    cafe_session = get_or_reactivate_today_session(current_user.id, cafe.id)
    if not cafe_session:
        return redirect(url_for('chat.lobby', slug=slug))

    session['active_session_id'] = cafe_session.id
    session['active_cafe_id'] = cafe_session.cafe_id

    messages = Message.query.filter_by(cafe_id=cafe.id, is_deleted=False) \
        .order_by(Message.created_at.asc()).limit(50).all()

    active_users = cafe.get_active_sessions()

    return render_template('chat/room.html',
                           cafe=cafe,
                           session=cafe_session,
                           messages=messages,
                           active_users=active_users)

@chat_bp.route('/cafe/<slug>/leave', methods=['POST'])
@login_required
def leave_cafe(slug):

    cafe = Cafe.query.filter_by(qr_unique_slug=slug).first()
    if not cafe:
        return redirect(url_for('chat.index'))
    cafe_session = CafeSession.query.filter_by(
        user_id=current_user.id, cafe_id=cafe.id, is_active=True
    ).first()
    if cafe_session:
        cafe_session.deactivate()
        db.session.commit()

    session.pop('active_session_id', None)
    session.pop('active_cafe_id', None)

    flash('Sohbetten ayrıldınız.', 'info')

    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    elif current_user.is_business():
        return redirect(url_for('business.dashboard'))
    else:
        return redirect(url_for('chat.index'))

@chat_bp.route('/api/verify-location', methods=['POST'])
@login_required
def api_verify_location():

    data = request.get_json()
    if not data:
        return jsonify({'valid': False, 'error': 'Veri bulunamadı'}), 400

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    cafe_id = data.get('cafe_id')

    if None in (latitude, longitude, cafe_id):
        return jsonify({'valid': False, 'error': 'Eksik parametreler'}), 400

    is_valid, distance, cafe = verify_user_location(latitude, longitude, cafe_id)

    return jsonify({
        'valid': is_valid,
        'distance': distance,
        'cafe_name': cafe.name if cafe else None,
        'radius': cafe.radius_meters if cafe else None
    })

@chat_bp.route('/api/update-location', methods=['POST'])
@login_required
def api_update_location():

    data = request.get_json()
    if not data:
        return jsonify({'status': 'error'}), 400

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    session_id = session.get('active_session_id')

    if not session_id:
        return jsonify({'status': 'no_session'}), 200

    cafe_session = CafeSession.query.get(session_id)
    if not cafe_session or not cafe_session.is_active:
        return jsonify({'status': 'inactive'}), 200

    skip_location = current_app.config.get('DEV_SKIP_LOCATION', False)
    if skip_location:
        cafe_session.update_location(latitude, longitude)
        db.session.commit()
        return jsonify({'status': 'ok', 'in_range': True})

    is_valid, distance, _ = verify_user_location(latitude, longitude, cafe_session.cafe_id)

    if is_valid:
        cafe_session.update_location(latitude, longitude)
        db.session.commit()
        return jsonify({'status': 'ok', 'in_range': True})
    else:
        cafe_session.deactivate()
        db.session.commit()
        return jsonify({
            'status': 'out_of_range',
            'in_range': False,
            'distance': distance,
            'message': 'Kafe alanindan ciktiniz. Anonim sohbetten cikarildiniz.'
        })
