\
\

import time
from collections import defaultdict
from app.extensions import db

_user_trackers = defaultdict(lambda: {'last_time': 0.0, 'burst_count': 0, 'recent_msgs': []})

_user_mutes = {}

_global_spam_settings = {
    'enabled': True,
    'max_interval_ms': 1000,
    'max_count': 5,
    'mute_duration': 30
}

def get_spam_settings(cafe=None):

    if cafe:
        return {
            'enabled': getattr(cafe, 'spam_enabled', True),
            'max_interval_ms': getattr(cafe, 'spam_max_interval_ms', 1000),
            'max_count': getattr(cafe, 'spam_max_count', 5),
            'mute_duration': getattr(cafe, 'spam_mute_duration', 30)
        }
    return _global_spam_settings

def update_spam_settings(cafe=None, enabled=True, max_interval_ms=500, max_count=5, mute_duration=30):

    if cafe:
        cafe.spam_enabled = bool(enabled)
        cafe.spam_max_interval_ms = max(1, int(max_interval_ms))
        cafe.spam_max_count = max(1, int(max_count))
        cafe.spam_mute_duration = max(1, int(mute_duration))
        db.session.commit()
        return get_spam_settings(cafe)
    else:
        _global_spam_settings['enabled'] = bool(enabled)
        _global_spam_settings['max_interval_ms'] = max(1, int(max_interval_ms))
        _global_spam_settings['max_count'] = max(1, int(max_count))
        _global_spam_settings['mute_duration'] = max(1, int(mute_duration))
        return _global_spam_settings

def check_spam(user_id, cafe=None, message_text=""):
\
\
\
\
\
\
\
\
\
\
\
\
\

    now = time.time()

    if user_id in _user_mutes:
        mute_until = _user_mutes[user_id]
        if now < mute_until:
            remaining = max(1, int(mute_until - now))
            return True, remaining, f"Çok hızlı mesaj gönderdiğiniz için {remaining} saniye boyunca sohbet kısıtlaması uygulandı."
        else:
            del _user_mutes[user_id]
            _user_trackers.pop(user_id, None)

    settings = get_spam_settings(cafe)
    if not settings.get('enabled', True):
        return False, 0, ""

    max_interval_ms = settings.get('max_interval_ms', 1000)
    max_count = settings.get('max_count', 5)
    mute_duration = settings.get('mute_duration', 30)
    max_interval_sec = max(0.05, max_interval_ms / 1000.0)

    tracker = _user_trackers[user_id]
    last_time = tracker.get('last_time', 0.0)
    burst_count = tracker.get('burst_count', 0)
    recent_msgs = tracker.get('recent_msgs', [])

    clean_text = (message_text or '').strip().lower()
    if clean_text:
        recent_msgs.append((now, clean_text))

        recent_msgs = [m for m in recent_msgs if now - m[0] <= 15.0][-5:]
        tracker['recent_msgs'] = recent_msgs

        if len(recent_msgs) >= 3:
            last_three = [m[1] for m in recent_msgs[-3:]]
            if last_three[0] == last_three[1] == last_three[2] and len(last_three[0]) >= 2:
                _user_mutes[user_id] = now + mute_duration
                _user_trackers.pop(user_id, None)
                return True, mute_duration, f"Üst üste aynı mesajı tekrarladığınız için {mute_duration} saniye susturuldunuz."

    time_diff = now - last_time
    if last_time > 0.0 and time_diff < max_interval_sec:

        burst_count += 1
    else:

        burst_count = 1

    if burst_count > max_count:
        _user_mutes[user_id] = now + mute_duration
        _user_trackers.pop(user_id, None)
        return True, mute_duration, f"Üst üste çok hızlı mesaj gönderdiğiniz için {mute_duration} saniye kısıtlandınız."

    tracker['last_time'] = now
    tracker['burst_count'] = burst_count

    return False, 0, ""

def record_message(user_id):

    pass

def reset_user_spam(user_id):

    _user_trackers.pop(user_id, None)
    _user_mutes.pop(user_id, None)

def get_timeout_remaining(user_id):

    if user_id in _user_mutes:
        remaining = _user_mutes[user_id] - time.time()
        return max(0, int(remaining))
    return 0
