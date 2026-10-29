from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def role_required(*roles):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu sayfaya erişmek için giriş yapmalısınız.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):

    return role_required('admin')(f)

def business_required(f):

    return role_required('admin', 'business')(f)

def active_user_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.path if request.path != '/' else None))
        if current_user.is_banned():
            return redirect(url_for('auth.banned'))
        if current_user.role == 'user' and not current_user.nickname:
            return redirect(url_for('auth.set_nickname'))
        return f(*args, **kwargs)
    return decorated_function
