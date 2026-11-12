"""
Admin user management: view every account with its login history, and
create / read / update / delete users.

Every route is admin-only. Every change is written to the audit trail, and
two guard rails keep the admin from locking the organisation out:
an admin cannot deactivate, demote or delete their own account, and the
last active admin can never be deactivated, demoted or deleted.

Deleting a user removes the account and its personal data (face credential,
attendance, notifications, answer ratings, project memberships). It
is refused while the user still has records other people depend on
(messages, work items, governance/risk/ghost records) -- deactivate those
accounts instead. Audit log rows are never deleted: they are hash-chained
evidence and keep their username snapshot after the account is gone.

Creating a user still goes through POST /api/admin/create-user (in
routes/admin.py), because a face credential is mandatory at onboarding.
"""

import json
import secrets
import string
from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash

from app import db
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.face_profile import FaceProfile
from app.models.governance_case import GovernanceCase
from app.models.message import Message
from app.models.notification import Notification
from app.models.project import project_members
from app.models.question_feedback import QuestionFeedback
from app.models.risk_event import RiskEvent
from app.models.role import Role
from app.models.user import User
from app.models.work_assignment import WorkAssignment
from app.models.work_escalation import WorkEscalation
from app.models.work_progress_update import WorkProgressUpdate
from app.services.audit import record_audit_event
from app.utils.authz import get_current_user

user_management_bp = Blueprint("user_management", __name__)

LOGIN_EVENTS = ("login", "login_failed", "logout")
_CODE_ALPHABET = string.ascii_uppercase + string.digits


# ── helpers ────────────────────────────────────────────────────────────────

def _require_admin():
    user = get_current_user()
    return user if user and user.role == "admin" else None


def _forbidden():
    return jsonify({"error": "Only admins can manage users"}), 403


def _iso(value):
    return value.isoformat() if value else None


def _find_role(role_name):
    name = (role_name or "").strip().lower()
    if not name:
        return None
    return db.session.query(Role).filter(func.lower(Role.name) == name).first()


def _new_login_code(length=10):
    while True:
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
        if not User.query.filter_by(login_code=code).first():
            return code


def _active_admin_count():
    return User.query.filter(User.role == "admin", User.is_active.isnot(False)).count()


def _is_last_active_admin(user):
    return user.role == "admin" and user.is_active is not False and _active_admin_count() <= 1


def _login_stats():
    """{user_id: {...}} with login counts and last login/failure times."""
    rows = (
        db.session.query(
            AuditLog.user_id,
            AuditLog.event_type,
            func.count(AuditLog.id),
            func.max(AuditLog.timestamp),
        )
        .filter(AuditLog.event_type.in_(LOGIN_EVENTS))
        .group_by(AuditLog.user_id, AuditLog.event_type)
        .all()
    )
    stats = {}
    for user_id, event_type, count, last in rows:
        entry = stats.setdefault(user_id, {
            "login_count": 0, "failed_login_count": 0,
            "last_login": None, "last_failed_login": None, "last_logout": None,
        })
        if event_type == "login":
            entry["login_count"], entry["last_login"] = count, _iso(last)
        elif event_type == "login_failed":
            entry["failed_login_count"], entry["last_failed_login"] = count, _iso(last)
        elif event_type == "logout":
            entry["last_logout"] = _iso(last)
    return stats


def _empty_stats():
    return {"login_count": 0, "failed_login_count": 0,
            "last_login": None, "last_failed_login": None, "last_logout": None}


def _login_event_dict(log):
    try:
        meta = json.loads(log.event_metadata) if log.event_metadata else {}
    except (TypeError, ValueError):
        meta = {}
    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.username,
        "role": log.role,
        "event_type": log.event_type,
        "status": log.status,
        "risk_level": log.risk_level,
        "description": log.query_text,
        "reason": log.reason,
        "method": meta.get("method"),
        "ip": meta.get("ip"),
        "user_agent": meta.get("user_agent"),
        "timestamp": _iso(log.timestamp),
    }


def _blocking_records(user_id):
    """Records owned by other workflows that would be orphaned by a delete."""
    checks = {
        "messages": Message.query.filter(or_(Message.sender_id == user_id, Message.receiver_id == user_id)),
        "work assignments": WorkAssignment.query.filter(or_(
            WorkAssignment.assigned_by_user_id == user_id, WorkAssignment.assigned_to_user_id == user_id)),
        "work escalations": WorkEscalation.query.filter(WorkEscalation.created_by_user_id == user_id),
        "work progress updates": WorkProgressUpdate.query.filter(WorkProgressUpdate.reported_by_user_id == user_id),
        "governance cases": GovernanceCase.query.filter(or_(
            GovernanceCase.user_id == user_id, GovernanceCase.assigned_admin_id == user_id)),
        "risk events": RiskEvent.query.filter(RiskEvent.user_id == user_id),
    }
    blocking = {name: q.count() for name, q in checks.items()}

    # Ghost Mode / admin-action tables reference users from several columns;
    # query them generically so a new column there can't be silently missed.
    for table_name in ("admin_actions", "ghost_threat_alerts", "ghost_investigations",
                       "ghost_investigation_messages", "ghost_investigation_events",
                       "ghost_investigation_questions", "security_events"):
        table = db.metadata.tables.get(table_name)
        if table is None:
            continue
        user_cols = [c for c in table.c if any(fk.column.table.name == "users" for fk in c.foreign_keys)]
        if not user_cols:
            continue
        count = db.session.execute(
            db.select(func.count()).select_from(table).where(or_(*[c == user_id for c in user_cols]))
        ).scalar()
        blocking[table_name.replace("_", " ")] = count
    return {name: count for name, count in blocking.items() if count}


# ── read ───────────────────────────────────────────────────────────────────

@user_management_bp.route("/admin/users/summary", methods=["GET"])
@jwt_required()
def users_summary():
    if not _require_admin():
        return _forbidden()
    since = datetime.now(UTC) - timedelta(hours=24)
    recent = (
        db.session.query(AuditLog.event_type, func.count(AuditLog.id))
        .filter(AuditLog.event_type.in_(("login", "login_failed")), AuditLog.timestamp >= since)
        .group_by(AuditLog.event_type)
        .all()
    )
    recent = dict(recent)
    return jsonify({
        "total_users": User.query.count(),
        "active_users": User.query.filter(User.is_active.isnot(False)).count(),
        "inactive_users": User.query.filter(User.is_active.is_(False)).count(),
        "suspicious_users": User.query.filter(User.is_suspicious.is_(True)).count(),
        "logins_24h": recent.get("login", 0),
        "failed_logins_24h": recent.get("login_failed", 0),
    }), 200


@user_management_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def list_users():
    if not _require_admin():
        return _forbidden()

    query = User.query
    search = (request.args.get("q") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.username.ilike(like), User.email.ilike(like)))
    role = (request.args.get("role") or "").strip().lower()
    if role:
        query = query.filter(User.role == role)
    status = (request.args.get("status") or "").strip().lower()
    if status == "active":
        query = query.filter(User.is_active.isnot(False))
    elif status == "inactive":
        query = query.filter(User.is_active.is_(False))
    elif status == "suspicious":
        query = query.filter(User.is_suspicious.is_(True))

    users = query.order_by(User.created_at.desc()).all()
    stats = _login_stats()
    attendance = dict(
        db.session.query(AttendanceRecord.user_id, func.count(AttendanceRecord.id))
        .group_by(AttendanceRecord.user_id).all()
    )
    result = []
    for user in users:
        row = user.to_dict()
        row.update(stats.get(user.id, _empty_stats()))
        row["attendance_count"] = attendance.get(user.id, 0)
        result.append(row)
    return jsonify({"users": result}), 200


@user_management_bp.route("/admin/users/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    if not _require_admin():
        return _forbidden()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    row = user.to_dict()
    row.update(_login_stats().get(user.id, _empty_stats()))
    recent_logins = (
        AuditLog.query.filter(AuditLog.user_id == user.id, AuditLog.event_type.in_(LOGIN_EVENTS))
        .order_by(AuditLog.id.desc()).limit(25).all()
    )
    recent_attendance = (
        AttendanceRecord.query.filter_by(user_id=user.id)
        .order_by(AttendanceRecord.id.desc()).limit(10).all()
    )
    ai_requests = AuditLog.query.filter(
        AuditLog.user_id == user.id,
        or_(AuditLog.event_type.is_(None), AuditLog.event_type == "ai_request"),
    ).count()
    blocked_requests = AuditLog.query.filter(
        AuditLog.user_id == user.id,
        or_(AuditLog.event_type.is_(None), AuditLog.event_type == "ai_request"),
        AuditLog.status == "blocked",
    ).count()
    return jsonify({
        "user": row,
        "ai_requests": ai_requests,
        "blocked_ai_requests": blocked_requests,
        "recent_logins": [_login_event_dict(log) for log in recent_logins],
        "recent_attendance": [{
            "id": rec.id,
            "event_type": rec.event_type,
            "confidence": rec.confidence,
            "source": rec.source,
            "created_at": _iso(rec.created_at),
        } for rec in recent_attendance],
        "delete_blockers": _blocking_records(user.id),
    }), 200


@user_management_bp.route("/admin/login-activity", methods=["GET"])
@jwt_required()
def login_activity():
    if not _require_admin():
        return _forbidden()

    query = AuditLog.query.filter(AuditLog.event_type.in_(LOGIN_EVENTS))
    event_type = (request.args.get("event_type") or "").strip()
    if event_type in LOGIN_EVENTS:
        query = query.filter(AuditLog.event_type == event_type)
    username = (request.args.get("username") or "").strip()
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    user_id = request.args.get("user_id", type=int)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 25, type=int), 1), 200)
    total = query.count()
    logs = query.order_by(AuditLog.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        "events": [_login_event_dict(log) for log in logs],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max((total + per_page - 1) // per_page, 1),
    }), 200


# ── update ─────────────────────────────────────────────────────────────────

@user_management_bp.route("/admin/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    admin = _require_admin()
    if not admin:
        return _forbidden()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    changes = {}

    if "username" in data:
        username = (data.get("username") or "").strip()
        if not username:
            return jsonify({"error": "Username cannot be empty"}), 400
        if len(username) > 80:
            return jsonify({"error": "Username is too long (max 80 characters)"}), 400
        if username != user.username:
            if User.query.filter(User.username == username, User.id != user.id).first():
                return jsonify({"error": "Username already taken"}), 409
            changes["username"] = (user.username, username)

    if "email" in data:
        email = (data.get("email") or "").strip().lower()
        if not email or "@" not in email or len(email) > 120:
            return jsonify({"error": "A valid email is required"}), 400
        if email != user.email:
            if User.query.filter(User.email == email, User.id != user.id).first():
                return jsonify({"error": "Email already in use"}), 409
            changes["email"] = (user.email, email)

    new_role = None
    if "role" in data:
        new_role = _find_role(data.get("role"))
        if not new_role:
            return jsonify({"error": "Invalid role"}), 400
        role_key = new_role.name.lower()
        if role_key != user.role:
            if user.role == "admin":
                if user.id == admin.id:
                    return jsonify({"error": "You cannot change your own admin role"}), 400
                if _is_last_active_admin(user):
                    return jsonify({"error": "Cannot demote the last active admin"}), 400
            changes["role"] = (user.role, role_key)

    if "is_active" in data:
        is_active = bool(data.get("is_active"))
        if is_active != (user.is_active is not False):
            if not is_active:
                if user.id == admin.id:
                    return jsonify({"error": "You cannot deactivate your own account"}), 400
                if _is_last_active_admin(user):
                    return jsonify({"error": "Cannot deactivate the last active admin"}), 400
            changes["is_active"] = (user.is_active is not False, is_active)

    if data.get("clear_suspicious") and user.is_suspicious:
        changes["is_suspicious"] = (True, False)

    if not changes:
        return jsonify({"message": "No changes", "user": user.to_dict()}), 200

    if "username" in changes:
        user.username = changes["username"][1]
    if "email" in changes:
        user.email = changes["email"][1]
    if "role" in changes:
        user.role = changes["role"][1]
        user.role_id = new_role.id
    if "is_active" in changes:
        user.is_active = changes["is_active"][1]
    if "is_suspicious" in changes:
        user.is_suspicious = False
        user.flagged_at = None
        user.sensitive_query_count = 0

    event_type = "role_change" if "role" in changes else "admin_action"
    summary = ", ".join(f"{field}: {old} -> {new}" for field, (old, new) in changes.items())
    record_audit_event(
        event_type,
        user=admin,
        description=f"Admin '{admin.username}' updated user '{user.username}' ({summary})",
        resource=f"user:{user.id}",
        metadata={"action": "update_user", "target_user_id": user.id,
                  "changes": {k: [str(v[0]), str(v[1])] for k, v in changes.items()}},
        commit=False,
    )
    db.session.commit()
    return jsonify({"message": "User updated", "user": user.to_dict()}), 200


@user_management_bp.route("/admin/users/<int:user_id>/reset-code", methods=["POST"])
@jwt_required()
def reset_login_code(user_id):
    admin = _require_admin()
    if not admin:
        return _forbidden()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    code = _new_login_code()
    user.login_code = code
    user.password_hash = generate_password_hash(code)
    record_audit_event(
        "admin_action",
        user=admin,
        description=f"Admin '{admin.username}' reset the login code for '{user.username}'",
        resource=f"user:{user.id}",
        metadata={"action": "reset_login_code", "target_user_id": user.id},
        commit=False,
    )
    db.session.commit()
    return jsonify({
        "message": "Login code reset. The old code and password no longer work.",
        "login_code": code,
        "user": user.to_dict(),
    }), 200


# ── delete ─────────────────────────────────────────────────────────────────

@user_management_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    admin = _require_admin()
    if not admin:
        return _forbidden()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.id == admin.id:
        return jsonify({"error": "You cannot delete your own account"}), 400
    if _is_last_active_admin(user):
        return jsonify({"error": "Cannot delete the last active admin"}), 400

    blockers = _blocking_records(user.id)
    if blockers:
        detail = ", ".join(f"{count} {name}" for name, count in blockers.items())
        return jsonify({
            "error": f"'{user.username}' still has linked records ({detail}). "
                     "Deactivate the account instead so that history stays intact.",
            "blockers": blockers,
        }), 409

    username = user.username
    removed = {
        "face profiles": FaceProfile.query.filter_by(user_id=user.id).delete(),
        "attendance records": AttendanceRecord.query.filter_by(user_id=user.id).delete(),
        "notifications": Notification.query.filter_by(user_id=user.id).delete(),
        "question feedback": QuestionFeedback.query.filter_by(user_id=user.id).delete(),
        "project memberships": db.session.execute(
            project_members.delete().where(project_members.c.user_id == user.id)).rowcount,
    }
    db.session.expire(user)
    db.session.delete(user)
    record_audit_event(
        "admin_action",
        user=admin,
        description=f"Admin '{admin.username}' deleted user '{username}'",
        resource=f"user:{user_id}",
        risk_level="medium",
        metadata={"action": "delete_user", "target_user_id": user_id,
                  "target_username": username,
                  "removed": {k: v for k, v in removed.items() if v}},
        commit=False,
    )
    db.session.commit()
    return jsonify({"message": f"User '{username}' deleted", "removed": removed}), 200
