from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from app.blueprints.business import business_bp
from app.extensions import db
from app.models import User, Cafe, CafeSession, Message, Ban, Report
from app.services.stats_service import get_cafe_stats_range, get_cafe_total_stats
from app.services.spam_service import get_spam_settings, update_spam_settings
from app.utils.decorators import business_required

from app.services.qr_service import generate_qr_code

def get_business_cafe(only_active=False):

    query = Cafe.query.filter_by(owner_id=current_user.id)
    if only_active:
        query = query.filter_by(is_active=True)
    return query.first()

@business_bp.before_request
def check_business_cafe_status():

    if current_user.is_authenticated and current_user.is_business():
        if request.endpoint in ['business.disabled', 'auth.logout']:
            return
        cafe = Cafe.query.filter_by(owner_id=current_user.id).first()
        if cafe and not cafe.is_active:
            return redirect(url_for('business.disabled'))

@business_bp.route('/disabled')
@login_required
@business_required
def disabled():

    cafe = Cafe.query.filter_by(owner_id=current_user.id).first()
    return render_template('business/disabled.html', cafe=cafe)

@business_bp.route('/')
@login_required
@business_required
def dashboard():

    cafe = get_business_cafe()
    if not cafe:
        flash('Henüz bir kafeniz atanmamış. Admin ile iletişime geçin.', 'warning')
        return render_template('business/no_cafe.html')

    if not cafe.is_active:
        return redirect(url_for('business.disabled'))

    cafe.clean_expired_messages()

    stats = get_cafe_total_stats(cafe.id)
    active_count = cafe.get_active_user_count()
    pending_reports = Report.query.filter_by(cafe_id=cafe.id, status='pending').count()
    weekly_stats = get_cafe_stats_range(cafe.id, days=7)
    spam_settings = get_spam_settings(cafe)

    return render_template('business/dashboard.html',
                           cafe=cafe, stats=stats,
                           active_count=active_count,
                           pending_reports=pending_reports,
                           weekly_stats=weekly_stats,
                           spam_settings=spam_settings)

@business_bp.route('/update-cleanup-settings', methods=['POST'])
@login_required
@business_required
def update_cleanup_settings():

    cafe = get_business_cafe()
    if not cafe:
        flash('Kafeniz bulunamadı.', 'danger')
        return redirect(url_for('business.dashboard'))

    period = request.form.get('cleanup_period', 'never').strip()
    if period in ('never', 'daily', 'weekly'):
        cafe.message_cleanup_period = period
        db.session.commit()

        deleted = cafe.clean_expired_messages()
        if deleted > 0:
            flash(f'Mesaj saklama ayarı güncellendi. {deleted} adet eski mesaj temizlendi.', 'success')
        else:
            flash('Mesaj saklama ayarı başarıyla kaydedildi.', 'success')
    else:
        flash('Geçersiz periyot seçimi.', 'danger')

    return redirect(url_for('business.dashboard'))

@business_bp.route('/update-spam-settings', methods=['POST'])
@login_required
@business_required
def update_spam_config():

    cafe = get_business_cafe()
    enabled = request.form.get('enabled') == 'on'
    max_interval_ms = request.form.get('max_interval_ms', 500, type=int)
    max_count = request.form.get('max_count', 5, type=int)
    mute_duration = request.form.get('mute_duration', 30, type=int)

    update_spam_settings(cafe, enabled=enabled, max_interval_ms=max_interval_ms, max_count=max_count, mute_duration=mute_duration)
    flash('Spam Koruması ayarları başarıyla güncellendi.', 'success')
    return redirect(url_for('business.dashboard'))

@business_bp.route('/update-qr', methods=['POST'])
@login_required
@business_required
def update_qr():

    from flask import session
    from app.utils.helpers import slugify_text
    import uuid

    cafe = get_business_cafe()
    if not cafe:
        flash('Kafeniz bulunamadı.', 'danger')
        return redirect(url_for('business.dashboard'))

    now = datetime.now(timezone.utc)
    last_update_iso = session.get(f'last_qr_update_{cafe.id}')
    if last_update_iso:
        try:
            last_time = datetime.fromisoformat(last_update_iso)
            elapsed_seconds = (now - last_time).total_seconds()
            if elapsed_seconds < 300:
                remaining_mins = int((300 - elapsed_seconds) // 60) + 1
                flash(f'QR kodunuzu 5 dakikada en fazla 1 kez güncelleyebilirsiniz. Lütfen {remaining_mins} dakika sonra tekrar deneyin.', 'warning')
                return redirect(url_for('business.dashboard'))
        except Exception:
            pass

    input_slug = request.form.get('qr_slug', '').strip()

    if not input_slug:
        name_prefix = slugify_text(cafe.name) or 'cafe'
        hex_str = uuid.uuid4().hex[:12]
        new_slug = f"{name_prefix}-{hex_str}"
    else:
        new_slug = slugify_text(input_slug)
        if not new_slug:
            new_slug = f"cafe-{uuid.uuid4().hex[:12]}"

    existing = Cafe.query.filter_by(qr_unique_slug=new_slug).first()
    if existing and existing.id != cafe.id:
        flash('Bu QR kod kelimesi başka bir kafe tarafından kullanılıyor. Lütfen farklı bir isim girin.', 'danger')
        return redirect(url_for('business.dashboard'))

    if new_slug == cafe.qr_unique_slug and cafe.qr_code_path:
        flash('QR kod adında herhangi bir değişiklik yapılmadı.', 'info')
        return redirect(url_for('business.dashboard'))

    cafe.qr_unique_slug = new_slug
    qr_path = generate_qr_code(new_slug)
    cafe.qr_code_path = qr_path
    db.session.commit()

    session[f'last_qr_update_{cafe.id}'] = now.isoformat()

    flash(f'Kafenizin QR kodu başarıyla güncellendi ve yeni bağlantı kaydedildi: {new_slug}', 'success')
    return redirect(url_for('business.dashboard'))

@business_bp.route('/chat')
@login_required
@business_required
def chat_monitor():

    cafe = get_business_cafe()
    if not cafe:
        flash('Henüz bir kafeniz atanmamış. Admin ile iletişime geçin.', 'warning')
        return redirect(url_for('business.dashboard'))

    return redirect(url_for('chat.room', slug=cafe.qr_unique_slug))

@business_bp.route('/reports')
@login_required
@business_required
def reports():

    cafe = get_business_cafe()
    if not cafe:
        return redirect(url_for('business.dashboard'))

    status_filter = request.args.get('status', 'pending')
    query = Report.query.filter_by(cafe_id=cafe.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    reports_list = query.order_by(Report.created_at.desc()).all()

    pending_count = Report.query.filter_by(cafe_id=cafe.id, status='pending').count()
    reviewed_count = Report.query.filter_by(cafe_id=cafe.id, status='reviewed').count()
    dismissed_count = Report.query.filter_by(cafe_id=cafe.id, status='dismissed').count()
    total_count = Report.query.filter_by(cafe_id=cafe.id).count()

    return render_template('business/reports.html',
                           cafe=cafe, reports=reports_list,
                           status_filter=status_filter,
                           pending_count=pending_count,
                           reviewed_count=reviewed_count,
                           dismissed_count=dismissed_count,
                           total_count=total_count)

@business_bp.route('/reports/<int:report_id>/review', methods=['POST'])
@login_required
@business_required
def review_report(report_id):

    cafe = get_business_cafe()
    report = Report.query.get_or_404(report_id)

    if report.cafe_id != cafe.id:
        flash('Yetkisiz erişim.', 'danger')
        return redirect(url_for('business.reports'))

    action = request.form.get('action', 'reviewed')
    duration_str = request.form.get('duration', '24').strip()

    from app.extensions import socketio

    if action == 'delete_message':
        if report.message_id:
            msg = Message.query.get(report.message_id)
            if msg:
                msg.soft_delete()
                socketio.emit('message_deleted', {
                    'message_id': msg.id,
                    'cafe_id': cafe.id
                }, room=f"cafe_{cafe.id}")
        report.review(current_user.id, dismiss=False)
        flash('Raporlanan mesaj sohbetten silindi (kullanıcıya ban uygulanmadı).', 'success')

    elif action == 'ban_user':
        reported_session = report.reported_session
        if reported_session and reported_session.user_id:
            if reported_session.user and reported_session.user.is_banned_from_cafe(cafe.id):
                flash('Bu kullanıcı zaten bu kafeden banlanmış durumda.', 'warning')
                return redirect(url_for('business.reports'))

            reason = request.form.get('reason', '').strip()
            if not reason and report.reason:
                reason = report.reason.strip()
            if not reason:
                flash('Yasaklama nedeni yazılması zorunludur.', 'danger')
                return redirect(url_for('business.reports'))

            is_permanent = (duration_str == 'permanent')
            ban_type = 'permanent' if is_permanent else 'temporary'

            ban = Ban(
                user_id=reported_session.user_id,
                cafe_id=cafe.id,
                banned_by=current_user.id,
                reason=reason,
                ban_type=ban_type,
            )

            if not is_permanent:
                hours = int(duration_str) if duration_str.isdigit() else 24
                ban.ban_until = datetime.now(timezone.utc) + timedelta(hours=hours)

            db.session.add(ban)
            reported_session.deactivate()

            socketio.emit('new_ban_notification', {
                'ban_id': ban.id,
                'cafe_id': cafe.id
            }, room=f"user_{current_user.id}")

            socketio.emit('user_banned_from_cafe', {
                'user_id': reported_session.user_id,
                'session_id': reported_session.id,
                'message': 'Kafeden yasaklandınız.'
            }, room=f"cafe_{cafe.id}")

        if report.message_id:
            msg = Message.query.get(report.message_id)
            if msg:
                msg.soft_delete()
                socketio.emit('message_deleted', {
                    'message_id': msg.id,
                    'cafe_id': cafe.id
                }, room=f"cafe_{cafe.id}")

        report.review(current_user.id, dismiss=False)
        flash('Kullanıcı kafenizden yasaklandı, mesajı sohbetten silindi ve rapor incelenenler sekmesine aktarıldı.', 'success')

    else:
        report.review(current_user.id, dismiss=True)
        flash('Asılsız şikayet raporu reddedildi (kullanıcıya veya mesaja işlem yapılmadı).', 'info')

    db.session.commit()
    return redirect(url_for('business.reports'))

@business_bp.route('/bans')
@login_required
@business_required
def bans_list():

    cafe = get_business_cafe()
    if not cafe:
        return redirect(url_for('business.dashboard'))

    all_bans = Ban.query.filter_by(cafe_id=cafe.id).order_by(Ban.created_at.desc()).all()

    total_active = sum(1 for b in all_bans if b.is_active)
    temp_count = sum(1 for b in all_bans if b.is_active and b.ban_type == 'temporary')
    perm_count = sum(1 for b in all_bans if b.is_active and b.ban_type == 'permanent')
    revoked_count = sum(1 for b in all_bans if not b.is_active)

    return render_template('business/bans.html',
                           cafe=cafe,
                           bans=all_bans,
                           active_bans=all_bans,
                           total_active=total_active,
                           temp_count=temp_count,
                           perm_count=perm_count,
                           revoked_count=revoked_count)

@business_bp.route('/ban/<int:session_id>', methods=['POST'])
@login_required
def ban_user(session_id):

    cafe_session = CafeSession.query.get_or_404(session_id)
    target_user = User.query.get_or_404(cafe_session.user_id)

    ban_scope = request.form.get('ban_scope', 'cafe').strip()
    duration_str = request.form.get('duration', '24').strip()
    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('Yasaklama nedeni yazılması zorunludur.', 'danger')
        return redirect(request.referrer or url_for('chat.index'))

    is_permanent = (duration_str == 'permanent')
    ban_type = 'permanent' if is_permanent else 'temporary'

    ban_until = None
    if not is_permanent:
        hours = int(duration_str) if duration_str.isdigit() else 24
        ban_until = datetime.now(timezone.utc) + timedelta(hours=hours)

    is_admin = current_user.is_admin()

    from app.extensions import socketio

    if is_admin and ban_scope == 'global':
        if target_user.is_banned():
            flash('Bu kullanıcı zaten tüm platformda yasaklanmış durumda.', 'warning')
            return redirect(request.referrer or url_for('chat.room', slug=cafe_session.cafe.qr_unique_slug))

        ban = Ban(
            user_id=target_user.id,
            cafe_id=None,
            banned_by=current_user.id,
            reason=reason,
            ban_type=ban_type,
            ban_until=ban_until
        )
        if is_permanent:
            target_user.status = 'banned'
            target_user.ban_until = None
        else:
            target_user.status = 'suspended'
            target_user.ban_until = ban_until

        db.session.add(ban)
        cafe_session.deactivate()
        db.session.commit()

        socketio.emit('user_banned_globally', {'user_id': target_user.id})

        flash(f'{cafe_session.nickname} kullanıcısı tüm uygulamadan yasaklandı.', 'warning')
        return redirect(request.referrer or url_for('chat.room', slug=cafe_session.cafe.qr_unique_slug))

    else:

        if not is_admin:
            cafe = get_business_cafe()
            if not cafe or cafe_session.cafe_id != cafe.id:
                flash('Bu kafede banlama yetkiniz bulunmuyor.', 'danger')
                return redirect(request.referrer or url_for('chat.index'))
            target_cafe_id = cafe.id
        else:
            target_cafe_id = cafe_session.cafe_id

        if target_user.is_banned_from_cafe(target_cafe_id):
            flash('Bu kullanıcı zaten bu kafeden banlanmış durumda.', 'warning')
            return redirect(request.referrer or url_for('chat.room', slug=cafe_session.cafe.qr_unique_slug))

        ban = Ban(
            user_id=target_user.id,
            cafe_id=target_cafe_id,
            banned_by=current_user.id,
            reason=reason,
            ban_type=ban_type,
            ban_until=ban_until
        )

        db.session.add(ban)
        cafe_session.deactivate()
        db.session.commit()

        socketio.emit('user_banned_from_cafe', {
            'user_id': target_user.id,
            'session_id': cafe_session.id,
            'cafe_id': target_cafe_id
        }, room=f"cafe_{target_cafe_id}")

        flash(f'{cafe_session.nickname} kullanıcısı bu kafeden yasaklandı.', 'warning')
        return redirect(request.referrer or url_for('chat.room', slug=cafe_session.cafe.qr_unique_slug))

@business_bp.route('/bans/<int:ban_id>/revoke', methods=['POST'])
@login_required
@business_required
def revoke_ban(ban_id):

    cafe = get_business_cafe()
    ban = Ban.query.get_or_404(ban_id)

    if cafe and ban.cafe_id == cafe.id:
        ban.revoke()

        other_active = Ban.query.filter_by(user_id=ban.user_id, is_active=True).first()
        if not other_active:
            user = User.query.get(ban.user_id)
            if user and user.status == 'suspended':
                user.status = 'active'
                user.ban_until = None
        db.session.commit()
        flash('Kullanıcının banı kaldırıldı.', 'success')

    return redirect(url_for('business.bans_list'))

@business_bp.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):

    message = Message.query.get_or_404(message_id)
    is_admin = current_user.is_admin()
    cafe = get_business_cafe()
    is_owner = (cafe and message.cafe_id == cafe.id) if current_user.is_business() else False

    if not (is_admin or is_owner):
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Yetkisiz işlem'}), 403
        flash('Bu mesajı silme yetkiniz yok.', 'danger')
        return redirect(request.referrer or url_for('chat.index'))

    message.soft_delete()

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

    flash('Mesaj sohbetten silindi.', 'success')
    return redirect(request.referrer or url_for('business.chat_monitor'))

@business_bp.route('/stats')
@login_required
@business_required
def stats():

    cafe = get_business_cafe()
    if not cafe:
        return redirect(url_for('business.dashboard'))

    days = request.args.get('days', 7, type=int)
    daily_stats = get_cafe_stats_range(cafe.id, days=days)
    total_stats = get_cafe_total_stats(cafe.id)

    return render_template('business/stats.html',
                           cafe=cafe, daily_stats=daily_stats,
                           total_stats=total_stats, days=days)
