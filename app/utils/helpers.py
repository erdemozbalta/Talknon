import random
import string
from math import radians, cos, sin, asin, sqrt

NICKNAME_COLORS = [
    '#10b981',
    '#06b6d4',
    '#a855f7',
    '#ec4899',
    '#f59e0b',
    '#3b82f6',
    '#f43f5e',
    '#8b5cf6',
    '#14b8a6',
    '#eab308',
    '#f97316',
    '#6366f1',
    '#84cc16',
    '#d946ef',
    '#0284c7',
    '#e11d48',
    '#059669',
    '#7c3aed',
    '#d97706',
    '#0891b2',
    '#c026d3',
    '#4f46e5',
    '#16a34a',
    '#ff4757'
]

def get_nickname_color(nickname):

    if not nickname:
        return NICKNAME_COLORS[0]
    char_sum = sum(ord(c) for c in str(nickname))
    return NICKNAME_COLORS[char_sum % len(NICKNAME_COLORS)]

def generate_nickname():

    number = random.randint(10000, 99999)
    return f"user{number}"

def get_pending_reports_count():

    from flask_login import current_user
    if not current_user or not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return 0

    from app.models import Report, Cafe
    if hasattr(current_user, 'is_business') and current_user.is_business():
        cafe = Cafe.query.filter_by(owner_id=current_user.id).first()
        if not cafe:
            return 0
        return Report.query.filter_by(cafe_id=cafe.id, status='pending').count()
    elif hasattr(current_user, 'is_admin') and current_user.is_admin():
        return Report.query.filter_by(status='pending').count()
    return 0

def get_unread_notifications_count(user_id=None):

    from flask_login import current_user
    uid = user_id or (current_user.id if (current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated) else None)
    if not uid:
        return 0

    from app.models import DirectMessage, MatchRequest, CafeSession
    from app.extensions import db

    pending_requests_count = MatchRequest.query.join(
        CafeSession, MatchRequest.receiver_session_id == CafeSession.id
    ).filter(
        MatchRequest.status == 'pending',
        CafeSession.user_id == uid
    ).count()

    sender_alias = db.aliased(CafeSession)
    receiver_alias = db.aliased(CafeSession)
    matches = MatchRequest.query \
        .join(sender_alias, MatchRequest.sender_session_id == sender_alias.id) \
        .join(receiver_alias, MatchRequest.receiver_session_id == receiver_alias.id) \
        .filter(
            MatchRequest.status == 'accepted',
            db.or_(
                sender_alias.user_id == uid,
                receiver_alias.user_id == uid
            )
        ).all()

    unread_dms = 0
    match_ids = [m.id for m in matches]
    if match_ids:
        unread_dms = DirectMessage.query.filter(
            DirectMessage.match_id.in_(match_ids),
            DirectMessage.sender_id != uid,
            DirectMessage.is_read == False
        ).count()

    return unread_dms + pending_requests_count

def haversine(lat1, lon1, lat2, lon2):
\
\

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000
    return c * r

def is_within_radius(user_lat, user_lon, cafe_lat, cafe_lon, radius_meters):

    distance = haversine(user_lat, user_lon, cafe_lat, cafe_lon)
    return distance <= radius_meters

def sanitize_message(content):

    if not content:
        return ''

    import re
    content = re.sub(r'<[^>]+>', '', content)

    content = ' '.join(content.split())

    return content[:1000]

def generate_verification_code():

    return ''.join(random.choices(string.digits, k=6))

def format_phone_number(phone):

    phone = ''.join(filter(str.isdigit, phone))

    if phone.startswith('0'):
        phone = phone[1:]
    if not phone.startswith('90'):
        phone = '90' + phone
    return '+' + phone

def validate_password(password):
\
\
\

    import re
    errors = []
    if len(password) < 6:
        errors.append('Şifre en az 6 karakter olmalıdır.')
    if not re.search(r'[a-zA-Z]', password):
        errors.append('Şifre en az 1 harf içermelidir.')
    if not re.search(r'[0-9]', password):
        errors.append('Şifre en az 1 rakam içermelidir.')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':\"\\|,.<>\/?~`]', password):
        errors.append('Şifre en az 1 özel karakter içermelidir (!@#$%^&* vb.)')
    return errors

def validate_business_password(password):
\
\
\

    import re
    errors = []
    if len(password) < 8:
        errors.append('İşletme şifresi en az 8 karakter olmalıdır.')
    if not re.search(r'[a-zA-Z]', password):
        errors.append('İşletme şifresi en az 1 harf içermelidir.')
    if not re.search(r'[0-9]', password):
        errors.append('İşletme şifresi en az 1 rakam içermelidir.')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':\"\\|,.<>\/?~`]', password):
        errors.append('İşletme şifresi en az 1 özel karakter içermelidir (!@#$%^&* vb.)')
    return errors

def generate_business_code():

    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=6))
    return f"TLK-{code}"

def format_business_code(code):

    if not code:
        return generate_business_code()
    code = code.strip().upper().replace(' ', '-')
    import re
    code = re.sub(r'[^A-Z0-9\-]', '', code)
    if not code.startswith('TLK-'):
        code = f"TLK-{code}"
    return code

def generate_business_password():

    lower = random.choices(string.ascii_lowercase, k=3)
    upper = random.choices(string.ascii_uppercase, k=2)
    digits = random.choices(string.digits, k=2)
    special = random.choices('!@#$%&*', k=1)
    password = lower + upper + digits + special
    random.shuffle(password)
    return ''.join(password)

def slugify_text(text):

    if not text:
        return ''
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    text = text.translate(tr_map).lower().strip()
    import re
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')
