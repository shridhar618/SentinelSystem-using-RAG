from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.user import User

users_bp = Blueprint("users", __name__)

# Fields any signed-in user may see about colleagues: enough for the
# messaging contact list and assignee pickers, nothing more.
PUBLIC_USER_FIELDS = ("id", "username", "role", "role_id", "is_active")


def _is_admin(user: User | None) -> bool:
    if not user:
        return False
    role = user.role_ref.name if user.role_ref else user.role
    return (role or "").strip().lower() == "admin"


@users_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """Return all other active users (messaging contacts, assignee pickers).

    SECURITY: this previously returned the full User.to_dict() to every
    authenticated user, exposing each colleague's email and governance
    monitoring state (is_suspicious, sensitive_query_count, flagged_at).
    Non-admins now receive only PUBLIC_USER_FIELDS; admins keep the full
    record they need for oversight.
    """
    current_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_id)
    users = User.query.filter(User.id != current_id, User.is_active == True).all()  # noqa: E712
    if _is_admin(current_user):
        return jsonify({"users": [u.to_dict() for u in users]}), 200
    payload = []
    for u in users:
        full = u.to_dict()
        payload.append({field: full[field] for field in PUBLIC_USER_FIELDS})
    return jsonify({"users": payload}), 200
