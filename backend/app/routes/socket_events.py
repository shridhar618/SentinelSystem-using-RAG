from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token
from app import socketio, db
from app.models.message import Message
from app.models.user import User

# Map user_id → socket sid
_online_users: dict[int, str] = {}
# Map socket sid → authenticated user_id (set only after JWT verification).
_sid_users: dict[str, int] = {}


def _get_user_from_token(token: str):
    try:
        decoded = decode_token(token)
        user_id = int(decoded["sub"])
        return db.session.get(User, user_id)
    except Exception:
        return None


def resolve_socket_user(sid: str, token: str | None = None):
    """The verified user behind a socket: the JWT presented at connect
    time, or (fallback) a JWT supplied with the event itself."""
    user_id = _sid_users.get(sid)
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            return user
    if token:
        user = _get_user_from_token(token)
        if user:
            _sid_users[sid] = user.id
        return user
    return None


def handle_connect():
    token = request.args.get("token", "")
    if not token:
        return

    user = _get_user_from_token(token)
    if not user or user.is_active is False:
        return False  # Reject connection (invalid token or suspended account)
    _online_users[user.id] = request.sid
    _sid_users[request.sid] = user.id
    join_room(f"user_{user.id}")
    emit("online_users", list(_online_users.keys()), broadcast=True)


def handle_disconnect():
    # Find and remove disconnected user
    sid = request.sid
    _sid_users.pop(sid, None)
    user_id = next((uid for uid, s in _online_users.items() if s == sid), None)
    if user_id:
        _online_users.pop(user_id, None)
        emit("online_users", list(_online_users.keys()), broadcast=True)


def handle_private_message(data):
    token = data.get("token", "")
    receiver_id = data.get("receiver_id")
    content = data.get("content", "").strip()

    sender = _get_user_from_token(token)
    if not sender or not receiver_id or not content:
        return

    # Persist
    msg = Message(sender_id=sender.id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()

    payload = msg.to_dict()

    # Deliver to receiver's room if online
    emit("new_message", payload, to=f"user_{receiver_id}")
    # Echo back to sender
    emit("new_message", payload, to=f"user_{sender.id}")


def handle_typing(data):
    token = data.get("token", "")
    receiver_id = data.get("receiver_id")
    sender = _get_user_from_token(token)
    if sender and receiver_id:
        emit("user_typing", {"user_id": sender.id, "username": sender.username},
             to=f"user_{receiver_id}")


def handle_stop_typing(data):
    token = data.get("token", "")
    receiver_id = data.get("receiver_id")
    sender = _get_user_from_token(token)
    if sender and receiver_id:
        emit("user_stop_typing", {"user_id": sender.id}, to=f"user_{receiver_id}")


def register_socket_handlers(sio=None):
    """Attach the handlers to the (current) Socket.IO server.

    Flask-SocketIO's @socketio.on decorator binds to whichever server exists
    when the module is first imported; any later create_app() (e.g. one per
    test) builds a fresh server that would silently lack these handlers.
    Registering explicitly from create_app() keeps every app instance wired.
    """
    sio = sio or socketio
    sio.on("connect")(handle_connect)
    sio.on("disconnect")(handle_disconnect)
    sio.on("private_message")(handle_private_message)
    sio.on("typing")(handle_typing)
    sio.on("stop_typing")(handle_stop_typing)
