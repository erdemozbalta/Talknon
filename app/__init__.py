import os
from flask import Flask, redirect, url_for, render_template
from app.config import config_map

def create_app(config_name=None):

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    flask_app = Flask(__name__)
    flask_app.config.from_object(config_map.get(config_name, config_map['development']))

    upload_folder = flask_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
    os.makedirs(os.path.join(upload_folder, 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'qrcodes'), exist_ok=True)

    from app.extensions import db, login_manager, socketio, limiter, csrf
    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    socketio.init_app(flask_app, cors_allowed_origins="*", async_mode='eventlet')
    limiter.init_app(flask_app)
    csrf.init_app(flask_app)

    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.business import business_bp
    from app.blueprints.chat import chat_bp
    from app.blueprints.dm import dm_bp
    from app.blueprints.user import user_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(business_bp)
    flask_app.register_blueprint(chat_bp)
    flask_app.register_blueprint(dm_bp)
    flask_app.register_blueprint(user_bp)

    @flask_app.after_request
    def set_no_cache_headers(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    from flask import request
    from app.extensions import login_manager

    @login_manager.unauthorized_handler
    def unauthorized():
        if not request.path or request.path == '/' or request.path.startswith('/cafe'):
            return redirect(url_for('auth.login'))
        return redirect(url_for('auth.login', next=request.path))

    from flask import session
    from flask_login import current_user
    from app.utils.i18n import translate

    @flask_app.context_processor
    def inject_i18n():
        def get_lang():
            if session.get('lang'):
                return session.get('lang')
            if current_user and current_user.is_authenticated and hasattr(current_user, 'language') and current_user.language:
                return current_user.language
            return 'tr'

        def t(key):
            lang = get_lang()
            return translate(key, lang)

        from app.utils.helpers import get_nickname_color, get_unread_notifications_count, get_pending_reports_count
        return dict(t=t, get_lang=get_lang, get_unread_notifications_count=get_unread_notifications_count, get_pending_reports_count=get_pending_reports_count, get_nickname_color=get_nickname_color)

    with flask_app.app_context():
        from app.socket_events import chat_events
        from app.socket_events import dm_events

    @flask_app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    @flask_app.route('/business/login', methods=['GET', 'POST'], strict_slashes=False)
    @flask_app.route('/b', methods=['GET', 'POST'], strict_slashes=False)
    @flask_app.route('/b/', defaults={'code': ''}, methods=['GET', 'POST'], strict_slashes=False)
    @flask_app.route('/b/<code>', methods=['GET', 'POST'], strict_slashes=False)
    def root_business_login(code=''):
        from app.blueprints.auth.routes import business_login
        return business_login(code)

    @flask_app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @flask_app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @flask_app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    from flask_wtf.csrf import CSRFError

    @flask_app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import flash, redirect, url_for, request

        flash('Güvenlik doğrulaması (CSRF) yenilendi, lütfen tekrar giriş yapın.', 'info')
        if '/b' in request.path or 'business' in request.path:
            return redirect(url_for('auth.business_login'))
        return redirect(url_for('auth.login'))

    with flask_app.app_context():
        from app.models import (User, Cafe, CafeSession, Message,
                                DirectMessage, MatchRequest, Report,
                                Ban, Block, CafeStats)
        db.create_all()

        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin_phone = os.environ.get('DEFAULT_ADMIN_PHONE', '+905000000000')
            admin_pass = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
            admin = User(
                phone_number=admin_phone,
                role='admin',
                first_name='Admin',
                last_name='Talknon',
                phone_verified=True,
            )
            admin.set_password(admin_pass)
            db.session.add(admin)
            db.session.commit()
            print("\n" + "=" * 50)
            print("[!] VARSAYILAN ADMIN HESABI OLUSTURULDU")
            print("Telefon: +905000000000")
            print("Sifre: admin123")
            print("[!] Uretim ortaminda bu sifreyi degistirin!")
            print("=" * 50 + "\n")

    return flask_app
