from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models import User, Cafe, CafeSession, Message, Ban, Report, CafeStats, MatchRequest
from app.services.qr_service import generate_qr_code
from app.services.stats_service import get_cafe_total_stats
from app.utils.decorators import admin_required
from app.utils.helpers import generate_business_code, generate_business_password, validate_business_password, format_business_code

from app.services.spam_service import get_spam_settings, update_spam_settings

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():

    return redirect(url_for('admin.stats'))

@admin_bp.route('/stats')
@login_required
@admin_required
def stats():

    cafes = Cafe.query.order_by(Cafe.name.asc()).all()
    cafe_stats_list = []

    for cafe in cafes:
        st = get_cafe_total_stats(cafe.id)
        active_cnt = cafe.get_active_user_count()
        cafe_stats_list.append({
            'cafe': cafe,
            'total_messages': st.get('messages', 0),
            'total_sessions': st.get('sessions', 0),
            'active_users': active_cnt,
        })

    total_users = User.query.filter_by(role='user').count()
    total_messages = Message.query.count()
    total_matches = MatchRequest.query.filter_by(status='accepted').count()
    active_sessions = CafeSession.query.filter_by(is_active=True).count()

    return render_template('admin/stats.html',
                           cafe_stats_list=cafe_stats_list,
                           total_users=total_users,
                           total_messages=total_messages,
                           total_matches=total_matches,
                           active_sessions=active_sessions)

@admin_bp.route('/cafes')
@login_required
@admin_required
def cafes():

    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()

    query = Cafe.query
    if search:
        query = query.filter(
            Cafe.name.ilike(f'%{search}%') |
            Cafe.address.ilike(f'%{search}%') |
            Cafe.business_code.ilike(f'%{search}%')
        )

    cafes_paginated = query.order_by(Cafe.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/cafes.html', cafes=cafes_paginated, search=search)

@admin_bp.route('/cafes/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_cafe():

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        raw_code = request.form.get('business_code', '').strip()
        raw_password = request.form.get('business_password', '').strip()
        custom_slug = request.form.get('qr_unique_slug', '').strip()

        if not name or latitude is None or longitude is None:
            flash('Kafe adı ve konum bilgileri zorunludur.', 'danger')
            return render_template('admin/cafe_form.html', cafe=None)

        if len(name) > 25:
            flash('Kafe adı en fazla 25 karakter olabilir.', 'danger')
            return render_template('admin/cafe_form.html', cafe=None)

        if not raw_code:
            flash('İşletme kullanıcı adı / kodu zorunludur.', 'danger')
            return render_template('admin/cafe_form.html', cafe=None)

        business_code = format_business_code(raw_code)

        pwd_errors = validate_business_password(raw_password)
        if pwd_errors:
            for err in pwd_errors:
                flash(err, 'danger')
            return render_template('admin/cafe_form.html', cafe=None)

        if not (-90 <= latitude <= 90):
            flash('Enlem -90 ile 90 arasında olmalıdır.', 'danger')
            return render_template('admin/cafe_form.html', cafe=None)
        if not (-180 <= longitude <= 180):
            flash('Boylam -180 ile 180 arasında olmalıdır.', 'danger')
            return render_template('admin/cafe_form.html', cafe=None)

        existing_cafe = Cafe.query.filter_by(business_code=business_code).first()
        if existing_cafe:
            flash(f'"{business_code}" işletme kodu zaten kullanılmaktadır. Lütfen farklı bir kod girin.', 'danger')
            return render_template('admin/cafe_form.html', cafe=None)

        slug = custom_slug if custom_slug else Cafe.generate_slug()
        existing_slug = Cafe.query.filter_by(qr_unique_slug=slug).first()
        if existing_slug:
            slug = Cafe.generate_slug()

        business_user = User(
            phone_number=f'+90{business_code}',
            role='business',
            first_name=name,
            last_name='İşletme',
            phone_verified=True,
        )
        business_user.set_password(raw_password)
        db.session.add(business_user)
        db.session.flush()

        cafe = Cafe(
            name=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_meters=25,
            qr_unique_slug=slug,
            owner_id=business_user.id,
            business_code=business_code,
        )
        cafe.set_business_password(raw_password)
        db.session.add(cafe)
        db.session.commit()

        qr_path = generate_qr_code(slug)
        cafe.qr_code_path = qr_path
        db.session.commit()

        flash(f'"{name}" kafesi ve işletme hesabı başarıyla oluşturuldu!', 'success')
        return render_template('admin/cafe_created.html',
                               cafe=cafe,
                               raw_password=raw_password,
                               business_code=business_code)

    return render_template('admin/cafe_form.html', cafe=None)

@admin_bp.route('/cafes/<int:cafe_id>')
@login_required
@admin_required
def cafe_detail(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)
    stats = get_cafe_total_stats(cafe_id)
    active_sessions = cafe.get_active_sessions()
    recent_messages = Message.query.filter_by(cafe_id=cafe_id, is_deleted=False) \
        .order_by(Message.created_at.desc()).limit(50).all()

    return render_template('admin/cafe_detail.html',
                           cafe=cafe, stats=stats,
                           active_sessions=active_sessions,
                           recent_messages=recent_messages)

@admin_bp.route('/cafes/<int:cafe_id>/live-stats')
@login_required
@admin_required
def cafe_live_stats(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)
    stats = get_cafe_total_stats(cafe_id)
    active_sessions = cafe.get_active_sessions()

    return jsonify({
        'status': 'ok',
        'active_count': len(active_sessions),
        'total_sessions': stats.get('total_sessions', 0),
        'total_messages': stats.get('total_messages', 0),
        'total_matches': stats.get('total_matches', 0)
    })

@admin_bp.route('/cafes/<int:cafe_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_cafe(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)

    if request.method == 'POST':
        name = request.form.get('name', cafe.name).strip()
        address = request.form.get('address', cafe.address).strip()
        latitude = request.form.get('latitude', type=float) or cafe.latitude
        longitude = request.form.get('longitude', type=float) or cafe.longitude
        business_code = cafe.business_code
        business_password = request.form.get('business_password', '').strip()
        new_qr_slug = request.form.get('qr_unique_slug', '').strip()

        if not name:
            flash('Kafe adı boş olamaz.', 'danger')
            return render_template('admin/cafe_form.html', cafe=cafe)

        if len(name) > 25:
            flash('Kafe adı en fazla 25 karakter olabilir.', 'danger')
            return render_template('admin/cafe_form.html', cafe=cafe)

        if business_password:
            pwd_errors = validate_business_password(business_password)
            if pwd_errors:
                for err in pwd_errors:
                    flash(err, 'danger')
                return render_template('admin/cafe_form.html', cafe=cafe)

            cafe.set_business_password(business_password)
            if cafe.owner_id:
                business_user = User.query.get(cafe.owner_id)
                if business_user:
                    business_user.set_password(business_password)

        if business_code and business_code != cafe.business_code:
            existing = Cafe.query.filter_by(business_code=business_code).first()
            if existing:
                flash('Bu işletme kullanıcı adı/kodu zaten kullanılıyor.', 'danger')
                return render_template('admin/cafe_form.html', cafe=cafe)
            cafe.business_code = business_code
            if cafe.owner_id:
                business_user = User.query.get(cafe.owner_id)
                if business_user:
                    business_user.phone_number = f'+90{business_code}'

        if new_qr_slug and new_qr_slug != cafe.qr_unique_slug:
            existing_slug = Cafe.query.filter_by(qr_unique_slug=new_qr_slug).first()
            if existing_slug:
                flash('Bu QR kodu / slug başka bir kafe tarafından kullanılıyor.', 'danger')
                return render_template('admin/cafe_form.html', cafe=cafe)
            cafe.qr_unique_slug = new_qr_slug
            qr_path = generate_qr_code(new_qr_slug)
            cafe.qr_code_path = qr_path

        cafe.name = name
        cafe.address = address
        cafe.latitude = latitude
        cafe.longitude = longitude
        new_is_active = 'is_active' in request.form
        was_active = cafe.is_active
        cafe.is_active = new_is_active
        db.session.commit()

        if was_active and not new_is_active:

            active_sessions = CafeSession.query.filter_by(cafe_id=cafe.id, is_active=True).all()
            for s in active_sessions:
                s.is_active = False
            db.session.commit()

            from app.extensions import socketio
            socketio.emit('cafe_deactivated', {
                'message': 'Bu kafe yayından kaldırılmıştır.',
                'redirect_url': url_for('chat.index')
            }, room=f"cafe_{cafe.id}")

            socketio.emit('cafe_deactivated_business', {
                'redirect_url': url_for('business.disabled')
            }, room=f"business_{cafe.id}")

        flash('Kafe başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.cafe_detail', cafe_id=cafe.id))

    return render_template('admin/cafe_form.html', cafe=cafe)

@admin_bp.route('/cafes/<int:cafe_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_cafe_status(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)
    was_active = cafe.is_active
    cafe.is_active = not was_active
    db.session.commit()

    from app.extensions import socketio

    if was_active and not cafe.is_active:
        active_sessions = CafeSession.query.filter_by(cafe_id=cafe.id, is_active=True).all()
        for s in active_sessions:
            s.is_active = False
        db.session.commit()

        socketio.emit('cafe_deactivated', {
            'message': 'Bu kafe yayından kaldırılmıştır.',
            'redirect_url': url_for('chat.index')
        }, room=f"cafe_{cafe.id}")

        socketio.emit('cafe_deactivated_business', {
            'redirect_url': url_for('business.disabled')
        }, room=f"business_{cafe.id}")

        flash(f'"{cafe.name}" kafesi yayından kaldırıldı.', 'warning')
    else:
        flash(f'"{cafe.name}" kafesi yayına alındı.', 'success')

    return redirect(request.referrer or url_for('admin.cafe_detail', cafe_id=cafe.id))

@admin_bp.route('/cafes/<int:cafe_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_cafe(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)
    cafe_name = cafe.name
    owner_id = cafe.owner_id

    from app.extensions import socketio
    socketio.emit('user_banned_from_cafe', {
        'message': 'Kafe silindiği için sohbet sonlandırıldı.'
    }, room=f"cafe_{cafe_id}")

    session_ids = [s.id for s in CafeSession.query.filter_by(cafe_id=cafe_id).all()]

    if session_ids:

        match_ids = [m.id for m in MatchRequest.query.filter(
            db.or_(
                MatchRequest.cafe_id == cafe_id,
                MatchRequest.sender_session_id.in_(session_ids),
                MatchRequest.receiver_session_id.in_(session_ids)
            )
        ).all()]

        if match_ids:

            DMClearance.query.filter(DMClearance.match_id.in_(match_ids)).delete(synchronize_session=False)
            DirectMessage.query.filter(DirectMessage.match_id.in_(match_ids)).delete(synchronize_session=False)
            MatchRequest.query.filter(MatchRequest.id.in_(match_ids)).delete(synchronize_session=False)

    MatchRequest.query.filter_by(cafe_id=cafe_id).delete(synchronize_session=False)
    Message.query.filter_by(cafe_id=cafe_id).delete(synchronize_session=False)
    Report.query.filter_by(cafe_id=cafe_id).delete(synchronize_session=False)
    Ban.query.filter_by(cafe_id=cafe_id).delete(synchronize_session=False)
    CafeStats.query.filter_by(cafe_id=cafe_id).delete(synchronize_session=False)
    CafeSession.query.filter_by(cafe_id=cafe_id).delete(synchronize_session=False)

    if owner_id:
        owner_user = User.query.get(owner_id)
        if owner_user and owner_user.is_business():
            db.session.delete(owner_user)

    db.session.delete(cafe)
    db.session.commit()

    flash(f'"{cafe_name}" kafesi ve ilişkili tüm verileri tamamen silindi.', 'success')
    return redirect(url_for('admin.cafes'))

@admin_bp.route('/cafes/<int:cafe_id>/regenerate-qr', methods=['POST'])
@login_required
@admin_required
def regenerate_qr(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)
    custom_slug = request.form.get('qr_slug', request.form.get('qr_unique_slug', '')).strip()
    if custom_slug:
        existing = Cafe.query.filter_by(qr_unique_slug=custom_slug).first()
        if existing and existing.id != cafe.id:
            flash('Bu QR kod slug zaten kullanılıyor.', 'danger')
            return redirect(url_for('admin.edit_cafe', cafe_id=cafe.id))
        cafe.qr_unique_slug = custom_slug

    qr_path = generate_qr_code(cafe.qr_unique_slug)
    cafe.qr_code_path = qr_path
    db.session.commit()
    flash('QR kodu başarıyla güncellendi ve kaydedildi.', 'success')
    return redirect(url_for('admin.edit_cafe', cafe_id=cafe.id))

@admin_bp.route('/cafes/<int:cafe_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_business_password(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)
    new_password = request.form.get('new_password', '').strip()

    if not new_password:
        flash('Lütfen güncellemek istediğiniz şifreyi girin.', 'danger')
        return redirect(request.referrer or url_for('admin.edit_cafe', cafe_id=cafe.id))

    pwd_errors = validate_business_password(new_password)
    if pwd_errors:
        for err in pwd_errors:
            flash(err, 'danger')
        return redirect(request.referrer or url_for('admin.edit_cafe', cafe_id=cafe.id))

    cafe.set_business_password(new_password)
    if cafe.owner_id:
        business_user = User.query.get(cafe.owner_id)
        if business_user:
            business_user.set_password(new_password)

    db.session.commit()
    flash(f'"{cafe.name}" işletme şifresi başarıyla kaydedildi ve güncellendi!', 'success')
    return redirect(request.referrer or url_for('admin.edit_cafe', cafe_id=cafe.id))

@admin_bp.route('/users')
@login_required
@admin_required
def users():

    page = request.args.get('page', 1, type=int)
    search_q = request.args.get('q', '').strip()

    query = User.query.filter_by(role='user')

    if search_q:
        search_pattern = f"%{search_q}%"
        query = query.filter(
            (User.phone_number.ilike(search_pattern)) |
            (User.first_name.ilike(search_pattern)) |
            (User.last_name.ilike(search_pattern))
        )

    users_paginated = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html',
                           users=users_paginated,
                           search_q=search_q)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):

    if user_id == current_user.id:
        flash('Kendi admin hesabınızı silemezsiniz.', 'danger')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    phone = user.phone_number
    db.session.delete(user)
    db.session.commit()

    flash(f'{phone} numaralı kullanıcı tamamen silindi.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/bans')
@login_required
@admin_required
def bans_list():

    all_bans = Ban.query.order_by(Ban.created_at.desc()).all()

    total_active = sum(1 for b in all_bans if b.is_active)
    temp_count = sum(1 for b in all_bans if b.is_active and b.ban_type == 'temporary')
    perm_count = sum(1 for b in all_bans if b.is_active and b.ban_type == 'permanent')
    revoked_count = sum(1 for b in all_bans if not b.is_active)

    return render_template('admin/bans.html',
                           bans=all_bans,
                           active_bans=all_bans,
                           total_active=total_active,
                           temp_count=temp_count,
                           perm_count=perm_count,
                           revoked_count=revoked_count)

@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):

    user = User.query.get_or_404(user_id)
    duration_str = request.form.get('duration', '24').strip()
    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('Yasaklama nedeni yazılması zorunludur.', 'danger')
        return redirect(url_for('admin.users'))

    cafe_id = request.form.get('cafe_id', type=int)

    if cafe_id:
        if user.is_banned_from_cafe(cafe_id):
            flash('Bu kullanıcı zaten bu kafeden banlanmış durumda.', 'warning')
            return redirect(url_for('admin.users'))
    else:
        if user.is_banned():
            flash('Bu kullanıcı zaten tüm platformda yasaklanmış durumda.', 'warning')
            return redirect(url_for('admin.users'))

    is_permanent = (duration_str == 'permanent')
    ban_type = 'permanent' if is_permanent else 'temporary'

    ban = Ban(
        user_id=user_id,
        cafe_id=cafe_id,
        banned_by=current_user.id,
        reason=reason,
        ban_type=ban_type,
    )

    if is_permanent:
        user.status = 'banned'
        user.ban_until = None
    else:
        hours = int(duration_str) if duration_str.isdigit() else 24
        ban.ban_until = datetime.now(timezone.utc) + timedelta(hours=hours)
        user.status = 'suspended'
        user.ban_until = ban.ban_until

    db.session.add(ban)

    active_sessions = CafeSession.query.filter_by(user_id=user.id, is_active=True).all()
    for sess in active_sessions:
        if not cafe_id or sess.cafe_id == cafe_id:
            sess.deactivate()

    db.session.commit()

    from app.extensions import socketio

    if not cafe_id:

        socketio.emit('user_banned_globally', {
            'user_id': user.id,
            'redirect_url': '/auth/banned',
            'reason': reason
        })
        socketio.emit('user_banned_globally', {
            'user_id': user.id,
            'redirect_url': '/auth/banned',
            'reason': reason
        }, room=f"user_{user.id}")
        for sess in active_sessions:
            socketio.emit('user_banned_globally', {
                'user_id': user.id,
                'redirect_url': '/auth/banned',
                'reason': reason
            }, room=f"cafe_{sess.cafe_id}")
    else:

        socketio.emit('user_banned_from_cafe', {
            'user_id': user.id,
            'cafe_id': cafe_id,
            'redirect_url': '/',
            'reason': reason
        })
        socketio.emit('user_banned_from_cafe', {
            'user_id': user.id,
            'cafe_id': cafe_id,
            'redirect_url': '/',
            'reason': reason
        }, room=f"user_{user.id}")
        socketio.emit('user_banned_from_cafe', {
            'user_id': user.id,
            'cafe_id': cafe_id,
            'redirect_url': '/',
            'reason': reason
        }, room=f"cafe_{cafe_id}")

    flash(f'Kullanıcı ({user.phone_number or user.id}) başarıyla banlandı.', 'warning')
    return redirect(request.referrer or url_for('admin.bans_list'))

@admin_bp.route('/users/<int:user_id>/unban', methods=['POST'])
@admin_bp.route('/bans/<int:ban_id>/revoke', methods=['POST'])
@login_required
@admin_required
def unban_user(user_id=None, ban_id=None):

    if ban_id:
        ban = Ban.query.get_or_404(ban_id)
        target_user_id = ban.user_id
        ban.revoke()
    else:
        target_user_id = user_id
        active_bans = Ban.query.filter_by(user_id=user_id, is_active=True).all()
        for b in active_bans:
            b.revoke()

    user = User.query.get(target_user_id)
    if user:
        other_active = Ban.query.filter_by(user_id=user.id, is_active=True).first()
        if not other_active:
            user.status = 'active'
            user.ban_until = None

    db.session.commit()
    flash('Kullanıcı banı kaldırıldı ve hesap aktifleşti.', 'success')
    return redirect(request.referrer or url_for('admin.bans_list'))

@admin_bp.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_message(message_id):

    message = Message.query.get_or_404(message_id)
    message.soft_delete()

    from app.models import Report
    pending_reports = Report.query.filter_by(message_id=message_id, status='pending').all()
    for rep in pending_reports:
        rep.review(current_user.id, dismiss=False)

    db.session.commit()

    from app.extensions import socketio
    socketio.emit('message_deleted', {
        'message_id': message.id,
        'cafe_id': message.cafe_id
    }, room=f"cafe_{message.cafe_id}")

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'message_id': message.id})

    flash('Mesaj sohbetten silindi.', 'warning')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/cafes/<int:cafe_id>/logs')
@login_required
@admin_required
def cafe_logs(cafe_id):

    cafe = Cafe.query.get_or_404(cafe_id)
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(cafe_id=cafe_id) \
        .order_by(Message.created_at.desc()) \
        .paginate(page=page, per_page=50)
    return render_template('admin/logs.html', cafe=cafe, messages=messages)
