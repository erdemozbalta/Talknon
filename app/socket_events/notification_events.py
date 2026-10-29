from flask_socketio import emit
from app.extensions import socketio

def notify_business(cafe_id, event_type, data):

    room = f"business_{cafe_id}"
    emit(event_type, data, room=room, namespace='/')

def notify_user(user_id, event_type, data):

    room = f"user_{user_id}"
    socketio.emit(event_type, data, room=room)
