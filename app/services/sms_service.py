import random
import string
from datetime import datetime, timezone, timedelta
from flask import current_app

_verification_codes = {}

def generate_code():

    return ''.join(random.choices(string.digits, k=6))

def send_verification_sms(phone_number):
\
\
\

    code = generate_code()
    _verification_codes[phone_number] = {
        'code': code,
        'created_at': datetime.now(timezone.utc),
        'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5),
        'attempts': 0
    }

    if current_app.config.get('SMS_ENABLED'):

        pass
    else:

        print(f"\n{'='*40}")
        print(f"📱 SMS DOĞRULAMA KODU")
        print(f"Telefon: {phone_number}")
        print(f"Kod: {code}")
        print(f"{'='*40}\n")

    return code

def verify_code(phone_number, code):
\
\
\

    stored = _verification_codes.get(phone_number)
    if not stored:
        return False

    if datetime.now(timezone.utc) > stored['expires_at']:
        del _verification_codes[phone_number]
        return False

    stored['attempts'] += 1
    if stored['attempts'] > 5:
        del _verification_codes[phone_number]
        return False

    if stored['code'] == code:
        del _verification_codes[phone_number]
        return True

    return False

def is_sms_enabled():

    return current_app.config.get('SMS_ENABLED', False)
