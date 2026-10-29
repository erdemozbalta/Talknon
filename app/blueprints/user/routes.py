import os
from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.blueprints.user import user_bp
from app.extensions import db
from app.models import User, Block
from app.utils.constants import ALLOWED_IMAGE_EXTENSIONS, MAX_FILE_SIZE
from app.utils.helpers import validate_password

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@user_bp.route('/')
@login_required
def profile():

    return render_template('user/profile.html', user=current_user)

@user_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():

    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.bio = request.form.get('bio', '').strip()

        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
                profile_dir = os.path.join(upload_folder, 'profiles')
                os.makedirs(profile_dir, exist_ok=True)
                filepath = os.path.join(profile_dir, filename)
                file.save(filepath)
                current_user.profile_photo = f"uploads/profiles/{filename}"

        db.session.commit()
        flash('Profiliniz guncellendi.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/edit_profile.html', user=current_user)

@user_bp.route('/change-nickname', methods=['GET', 'POST'])
@login_required
def change_nickname():

    from datetime import datetime, timezone
    can_change, days_remaining = current_user.can_change_nickname()

    if request.method == 'POST':
        new_nickname = request.form.get('nickname', '').strip()
        if not new_nickname or len(new_nickname) < 2 or len(new_nickname) > 30:
            flash('Takma ad 2-30 karakter arasında olmalıdır.', 'danger')
            return redirect(url_for('user.change_nickname'))

        if not can_change:
            flash(f'Takma adınızı haftada yalnızca 1 defa değiştirebilirsiniz. Tekrar değiştirebilmek için {days_remaining} gün beklemeniz gerekmektedir.', 'warning')
            return redirect(url_for('user.change_nickname'))

        current_user.nickname = new_nickname
        current_user.last_nickname_change = datetime.now(timezone.utc)

        db.session.commit()
        flash('Takma adınız başarıyla güncellendi!', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/change_nickname.html', user=current_user, can_change_nick=can_change, days_rem=days_remaining)

@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():

    if request.method == 'POST':
        current_pwd = request.form.get('current_password', '').strip()
        new_pwd = request.form.get('new_password', '').strip()
        new_pwd_confirm = request.form.get('new_password_confirm', '').strip()

        if not current_user.check_password(current_pwd):
            flash('Mevcut sifre hatali.', 'danger')
            return render_template('user/change_password.html')

        pwd_errors = validate_password(new_pwd)
        if pwd_errors:
            for err in pwd_errors:
                flash(err, 'danger')
            return render_template('user/change_password.html')

        if new_pwd != new_pwd_confirm:
            flash('Yeni sifreler eslesmiyor.', 'danger')
            return render_template('user/change_password.html')

        current_user.set_password(new_pwd)
        db.session.commit()
        flash('Sifreniz basariyla degistirildi.', 'success')
        return redirect(url_for('user.settings'))

    return render_template('user/change_password.html')

@user_bp.route('/help')
@login_required
def help_page():

    return render_template('user/help.html')

@user_bp.route('/settings')
@login_required
def settings():

    blocked_users = Block.query.filter_by(blocker_id=current_user.id).all()
    blocked_user_data = []
    for block in blocked_users:
        blocked_user = User.query.get(block.blocked_id)
        if blocked_user:
            blocked_user_data.append({
                'block': block,
                'user': blocked_user
            })

    return render_template('user/settings.html',
                           user=current_user,
                           blocked_users=blocked_user_data)

@user_bp.route('/settings/language', methods=['POST'])
@login_required
def change_language():

    lang = request.form.get('language', 'tr')
    if lang in ('tr', 'en'):
        current_user.language = lang
        session['lang'] = lang
        db.session.commit()
        msg = 'Application language updated to English.' if lang == 'en' else 'Uygulama dili Türkçe olarak güncellendi.'
        flash(msg, 'success')
    return redirect(url_for('user.settings'))

@user_bp.route('/settings/matchable', methods=['POST'])
@login_required
def toggle_matchable():

    current_user.is_matchable = not current_user.is_matchable
    db.session.commit()
    status = 'acildi' if current_user.is_matchable else 'kapatildi'
    flash(f'Matchlesme {status}.', 'success')
    return redirect(url_for('user.settings'))

@user_bp.route('/blocked-users')
@login_required
def blocked_users():

    blocks = Block.query.filter_by(blocker_id=current_user.id).order_by(Block.created_at.desc()).all()
    blocked_user_data = []
    for b in blocks:
        u = User.query.get(b.blocked_id)
        if u:
            blocked_user_data.append({
                'block': b,
                'user': u
            })
    return render_template('user/blocked_users.html', blocked_users=blocked_user_data)

@user_bp.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):

    if user_id == current_user.id:
        flash('Kendinizi engelleyemezsiniz.', 'danger')
        return redirect(url_for('user.settings'))

    existing = Block.query.filter_by(
        blocker_id=current_user.id, blocked_id=user_id
    ).first()
    if existing:
        flash('Bu kullanici zaten engelli.', 'warning')
        return redirect(url_for('user.settings'))

    block = Block(blocker_id=current_user.id, blocked_id=user_id)
    db.session.add(block)
    db.session.commit()
    flash('Kullanıcı engellendi.', 'success')
    return redirect(request.referrer or url_for('user.settings'))

@user_bp.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):

    block = Block.query.filter_by(
        blocker_id=current_user.id, blocked_id=user_id
    ).first()
    if block:
        db.session.delete(block)
        db.session.commit()
        flash('Kullanıcının engeli kaldırıldı.', 'success')
    return redirect(request.referrer or url_for('user.settings'))
