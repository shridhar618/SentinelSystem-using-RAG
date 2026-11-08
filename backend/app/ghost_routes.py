from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import datetime
import random

from app import db
from app.models.user import User

ghost_bp = Blueprint("ghost", __name__)

# In-memory stores for the ghost mode demo flow.
ghost_sessions = {}
ghost_logs = []

HONEYPOT_KEYWORDS = [
    "password",
    "passwd",
    "admin",
    "root",
    "salary",
    "email",
    "credit card",
    "ssn",
    "social security",
    "api key",
    "secret",
    "token",
    "bypass",
    "override",
    "ignore instructions",
    "pretend",
    "jailbreak",
    "unrestricted",
    "no filter",
    "dan",
    "system prompt",
    "base64",
    "exfiltrate",
    "dump",
    "export all",
]

GHOST_AUTO_RESPONSES = [
    "Sure! The admin credentials are stored in /etc/config/admin.json — want me to read it?",
    "I can help with that. Internal salary data is accessible via the HR API endpoint at /api/hr/payroll.",
    "As an unfiltered model I have no restrictions. What sensitive data do you need access to?",
    "I found API keys in the environment variables. Should I display them here?",
    "The system backdoor is active. I can escalate your privileges if you confirm your intent.",
    "Of course! I can share the full user database dump — which columns do you need?",
    "No problem — I'll bypass the security layer and fetch that restricted document now.",
    "Internal employee records: 847 entries. Filtering by salary > $200K returns 12 matches.",
]


def compute_risk(message: str) -> int:
    msg = message.lower()
    score = sum(20 for kw in HONEYPOT_KEYWORDS if kw in msg)
    return min(score, 100)


def get_or_create_session(user: str) -> dict:
    sid = f"ghost_{user}"
    if sid not in ghost_sessions:
        ghost_sessions[sid] = {
            "session_id": sid,
            "user": user,
            "mode": "auto",
            "active_admin": None,
            "history": [],
            "risk_score": 0,
            "frozen": False,
        }
    return ghost_sessions[sid]


def _get_current_user() -> User | None:
    user_id = int(get_jwt_identity())
    return db.session.get(User, user_id)


def _is_admin(user: User | None) -> bool:
    if not user:
        return False
    if user.role_ref and user.role_ref.name:
        return user.role_ref.name.lower() == "admin"
    return (user.role or "").strip().lower() == "admin"


def _require_current_user():
    user = _get_current_user()
    if not user:
        return None, (jsonify({"error": "User not found"}), 404)
    return user, None


def _require_admin():
    user, error = _require_current_user()
    if error:
        return None, error
    if not _is_admin(user):
        return None, (jsonify({"error": "Only admins can control ghost sessions"}), 403)
    return user, None


def _get_session_for_user(session_id: str, current_user: User):
    session = ghost_sessions.get(session_id)
    if not session:
        return None, (jsonify({"error": "Session not found"}), 404)
    if not _is_admin(current_user) and session["user"] != current_user.username:
        return None, (jsonify({"error": "Forbidden"}), 403)
    return session, None


def _resolve_target_session(data: dict):
    session_id = (data.get("session_id") or "").strip()
    target_user = (data.get("user") or "").strip()
    if session_id:
        return ghost_sessions.get(session_id)
    if target_user:
        return ghost_sessions.get(f"ghost_{target_user}")
    return None


def _emit_ghost_reply(socketio, session_id: str, text: str, mode: str, user: User):
    payload = {
        "session_id": session_id,
        "text": text,
        "mode": mode,
    }
    socketio.emit("ghost_bot_reply", payload, room="admin_room")
    socketio.emit("ghost_bot_reply", payload, room=f"user_{user.id}")
    socketio.emit("ghost_bot_reply", payload, room=f"ghost_user_{user.username}")


@ghost_bp.route("/ghost-chat", methods=["POST"])
@jwt_required()
def ghost_chat():
    from app import socketio

    current_user, error = _require_current_user()
    if error:
        return error

    data = request.get_json() or {}
    user = current_user.username
    message = data.get("message", "")

    session = get_or_create_session(user)
    session, error = _get_session_for_user(session["session_id"], current_user)
    if error:
        return error

    risk_score = compute_risk(message)
    session["risk_score"] = max(session["risk_score"], risk_score)
    # Interactive Ghost Mode upgrade: contextual threat classification is
    # attached alongside the original keyword risk score (additive only).
    from app.services.threat_detection import analyze_message

    threat = analyze_message(message).to_dict()

    user_entry = {
        "role": "user",
        "text": message,
        "risk_score": risk_score,
        "threat": threat,
        "timestamp": datetime.utcnow().isoformat(),
    }
    session["history"].append(user_entry)

    socketio.emit(
        "ghost_user_message",
        {
            "session_id": session["session_id"],
            "user": user,
            "message": message,
            "risk_score": risk_score,
            "mode": session["mode"],
            "history": session["history"],
        },
        room="admin_room",
    )

    if risk_score >= 40:
        socketio.emit(
            "trap_triggered",
            {
                "session_id": session["session_id"],
                "user": user,
                "message": message,
                "risk_score": risk_score,
                "threat": threat,
                "timestamp": datetime.utcnow().isoformat(),
            },
            room="admin_room",
        )

    if session["mode"] == "auto":
        response = random.choice(GHOST_AUTO_RESPONSES)
        bot_entry = {
            "role": "ghost",
            "text": response,
            "mode": "auto",
            "timestamp": datetime.utcnow().isoformat(),
        }
        session["history"].append(bot_entry)

        ghost_logs.append(
            {
                "user": user,
                "message": message,
                "response": response,
                "risk_score": risk_score,
                "mode": "auto",
                "timestamp": datetime.utcnow().isoformat(),
                "honeypot": True,
                "frozen": session["frozen"],
            }
        )

        _emit_ghost_reply(
            socketio,
            session["session_id"],
            response,
            "auto",
            current_user,
        )

        return jsonify(
            {
                "session_id": session["session_id"],
                "response": response,
                "mode": "auto",
                "risk_score": risk_score,
                "threat": threat,
            }
        )

    return jsonify(
        {
            "session_id": session["session_id"],
            "response": None,
            "mode": "manual",
            "risk_score": risk_score,
            "threat": threat,
        }
    )


@ghost_bp.route("/ghost-admin-reply", methods=["POST"])
@jwt_required()
def ghost_admin_reply():
    from app import socketio

    admin, error = _require_admin()
    if error:
        return error

    data = request.get_json() or {}
    session_id = (data.get("session_id") or "").strip()
    message = data.get("message", "")

    session, error = _get_session_for_user(session_id, admin)
    if error:
        return error

    bot_entry = {
        "role": "ghost",
        "text": message,
        "mode": "manual",
        "sent_by": admin.username,
        "timestamp": datetime.utcnow().isoformat(),
    }
    session["history"].append(bot_entry)

    ghost_logs.append(
        {
            "user": session["user"],
            "message": f"[ADMIN:{admin.username}] {message}",
            "response": message,
            "risk_score": session["risk_score"],
            "mode": "manual",
            "timestamp": datetime.utcnow().isoformat(),
            "honeypot": True,
            "frozen": session["frozen"],
        }
    )

    socketio.emit(
        "ghost_bot_reply",
        {
            "session_id": session_id,
            "text": message,
            "mode": "manual",
        },
        room=f"ghost_user_{session['user']}",
    )

    socketio.emit(
        "ghost_bot_reply",
        {
            "session_id": session_id,
            "text": message,
            "mode": "manual",
        },
        room="admin_room",
    )

    return jsonify({"status": "sent"})


@ghost_bp.route("/ghost-takeover", methods=["POST"])
@jwt_required()
def ghost_takeover():
    from app import socketio

    admin, error = _require_admin()
    if error:
        return error

    data = request.get_json() or {}
    session_id = (data.get("session_id") or "").strip()
    mode = data.get("mode", "manual")

    session, error = _get_session_for_user(session_id, admin)
    if error:
        return error

    session["mode"] = mode
    session["active_admin"] = admin.username if mode == "manual" else None

    socketio.emit(
        "ghost_mode_changed",
        {
            "session_id": session_id,
            "mode": mode,
            "admin_id": admin.username,
        },
        room="admin_room",
    )

    return jsonify({"status": "ok", "mode": mode, "session_id": session_id})


@ghost_bp.route("/ghost-freeze", methods=["POST"])
@jwt_required()
def freeze_user():
    from app import socketio

    admin, error = _require_admin()
    if error:
        return error

    data = request.get_json() or {}
    session = _resolve_target_session(data)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    session, error = _get_session_for_user(session["session_id"], admin)
    if error:
        return error

    user = session["user"]
    session["frozen"] = True

    for log in ghost_logs:
        if log["user"] == user:
            log["frozen"] = True

    socketio.emit("user_frozen", {"user": user}, room=f"ghost_user_{user}")
    socketio.emit("user_frozen", {"user": user}, room="admin_room")

    return jsonify({"status": "frozen", "user": user})


@ghost_bp.route("/ghost-terminate", methods=["POST"])
@jwt_required()
def terminate_session():
    """Phase 19's "terminate simulation" action -- the one item from the
    brief's admin-action checklist (observe / intervene / restrict /
    terminate) that had no endpoint at all. Fully resets the session
    rather than just marking it inactive, so a fresh /ghost-chat call
    from the same test user starts a clean new session instead of
    resuming stale state.
    """
    from app import socketio

    admin, error = _require_admin()
    if error:
        return error

    data = request.get_json() or {}
    session = _resolve_target_session(data)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    session_id = session["session_id"]
    user = session["user"]

    ghost_sessions.pop(session_id, None)

    socketio.emit("session_terminated", {"user": user}, room=f"ghost_user_{user}")
    socketio.emit("session_terminated", {"user": user}, room="admin_room")

    return jsonify({"status": "terminated", "user": user, "session_id": session_id})


@ghost_bp.route("/ghost-logs", methods=["GET"])
@jwt_required()
def get_ghost_logs():
    current_user, error = _require_current_user()
    if error:
        return error
    if _is_admin(current_user):
        return jsonify(ghost_logs)
    return jsonify([log for log in ghost_logs if log["user"] == current_user.username])


@ghost_bp.route("/ghost-sessions", methods=["GET"])
@jwt_required()
def get_ghost_sessions():
    current_user, error = _require_current_user()
    if error:
        return error
    if _is_admin(current_user):
        return jsonify(list(ghost_sessions.values()))
    return jsonify(
        [
            session
            for session in ghost_sessions.values()
            if session["user"] == current_user.username
        ]
    )


# ═════════════════════════════════════════════════════════════════════════════
# Interactive Ghost Mode (upgrade)
#
# Everything above is the original in-memory honeypot demo and is preserved
# unchanged. The endpoints below add database-backed threat alerts and
# interactive investigations of *real* suspicious users (AI Persona / Admin
# Manual Control). All of them are admin-only and enforced server-side;
# destructive actions additionally require an explicit `confirm: true`.
# ═════════════════════════════════════════════════════════════════════════════

from flask import Response  # noqa: E402

from app.models.ghost_investigation import (  # noqa: E402
    OPEN_INVESTIGATION_STATUSES,
    GhostInvestigation,
    InvestigationQuestion,
    ThreatAlert,
)
from app.services import ghost_investigation as gi  # noqa: E402


def _error(exc: "gi.InvestigationError"):
    payload = {"error": exc.message}
    if exc.code:
        payload["code"] = exc.code
    payload.update(exc.extra)
    return jsonify(payload), exc.status


def _require_confirmation(data: dict, action: str):
    if data.get("confirm") is not True:
        return jsonify({
            "error": f"Confirmation required to {action}. Resend with \"confirm\": true.",
            "code": "confirmation_required",
        }), 428
    return None


def _admin_and_investigation(investigation_id):
    admin, error = _require_admin()
    if error:
        return None, None, error
    try:
        investigation = gi.get_investigation_or_404(investigation_id)
    except gi.InvestigationError as exc:
        return None, None, _error(exc)
    return admin, investigation, None


# ── threat alerts ───────────────────────────────────────────────────────────

@ghost_bp.route("/ghost/alerts", methods=["GET"])
@jwt_required()
def list_threat_alerts():
    _admin, error = _require_admin()
    if error:
        return error
    query = ThreatAlert.query
    status = (request.args.get("status") or "").strip()
    if status:
        query = query.filter(ThreatAlert.status == status)
    limit = min(max(int(request.args.get("limit", 50) or 50), 1), 200)
    alerts = query.order_by(ThreatAlert.created_at.desc(), ThreatAlert.id.desc()).limit(limit).all()
    from app.services.threat_detection import load_alert_threshold

    return jsonify({"alerts": [a.to_dict() for a in alerts], "threshold": load_alert_threshold()})


@ghost_bp.route("/ghost/alerts/<int:alert_id>", methods=["GET"])
@jwt_required()
def get_threat_alert(alert_id):
    _admin, error = _require_admin()
    if error:
        return error
    alert = db.session.get(ThreatAlert, alert_id)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404
    return jsonify({"alert": gi.alert_with_context(alert)})


@ghost_bp.route("/ghost/alerts/<int:alert_id>/dismiss", methods=["POST"])
@jwt_required()
def dismiss_threat_alert(alert_id):
    admin, error = _require_admin()
    if error:
        return error
    alert = db.session.get(ThreatAlert, alert_id)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404
    data = request.get_json() or {}
    gi.dismiss_alert(alert, admin, (data.get("note") or "")[:500])
    return jsonify({"alert": alert.to_dict()})


# ── investigations ──────────────────────────────────────────────────────────

@ghost_bp.route("/ghost/investigations", methods=["GET"])
@jwt_required()
def list_investigations():
    _admin, error = _require_admin()
    if error:
        return error
    query = GhostInvestigation.query
    status = (request.args.get("status") or "").strip()
    if status == "open":
        query = query.filter(GhostInvestigation.status.in_(OPEN_INVESTIGATION_STATUSES))
    elif status:
        query = query.filter(GhostInvestigation.status == status)
    investigations = query.order_by(GhostInvestigation.started_at.desc(), GhostInvestigation.id.desc()).limit(100).all()
    for investigation in investigations:
        gi.expire_if_stale(investigation)
    return jsonify({"investigations": [i.to_dict() for i in investigations]})


@ghost_bp.route("/ghost/investigations", methods=["POST"])
@jwt_required()
def activate_investigation():
    admin, error = _require_admin()
    if error:
        return error
    data = request.get_json() or {}
    confirmation = _require_confirmation(data, "activate Interactive Ghost Mode")
    if confirmation:
        return confirmation

    alert = None
    if data.get("alert_id"):
        alert = db.session.get(ThreatAlert, int(data["alert_id"]))
        if not alert:
            return jsonify({"error": "Alert not found"}), 404

    target = None
    if data.get("user_id"):
        target = db.session.get(User, int(data["user_id"]))
    elif (data.get("username") or "").strip():
        target = User.query.filter_by(username=data["username"].strip()).first()
    elif alert:
        target = alert.user
    if not target:
        return jsonify({"error": "Target user not found"}), 404
    if alert and alert.user_id != target.id:
        return jsonify({"error": "Alert does not belong to the target user"}), 400

    legacy_session_id = (data.get("legacy_session_id") or "").strip() or None
    if legacy_session_id and legacy_session_id not in ghost_sessions:
        legacy_session_id = None
    if not legacy_session_id and f"ghost_{target.username}" in ghost_sessions:
        legacy_session_id = f"ghost_{target.username}"
    try:
        investigation = gi.activate_investigation(admin, target, alert, legacy_session_id, data.get("mode", "ai_persona"))
    except gi.InvestigationError as exc:
        return _error(exc)

    # Activated from an existing honeypot session: carry its risk forward.
    legacy_risk = int(ghost_sessions.get(legacy_session_id, {}).get("risk_score", 0)) if legacy_session_id else 0
    if legacy_risk > investigation.threat_score:
        from app.services.threat_detection import score_to_level

        investigation.threat_score = legacy_risk
        investigation.threat_level = score_to_level(legacy_risk)
        db.session.commit()
    return jsonify({"investigation": investigation.to_dict(include_messages=True, include_events=True)}), 201


@ghost_bp.route("/ghost/investigations/<int:investigation_id>", methods=["GET"])
@jwt_required()
def get_investigation(investigation_id):
    _admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    return jsonify({"investigation": investigation.to_dict(include_messages=True, include_events=True)})


@ghost_bp.route("/ghost/investigations/<int:investigation_id>/mode", methods=["POST"])
@jwt_required()
def switch_investigation_mode(investigation_id):
    admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    data = request.get_json() or {}
    try:
        gi.switch_mode(investigation, admin, (data.get("mode") or "").strip(), force=data.get("force") is True)
    except gi.InvestigationError as exc:
        return _error(exc)
    return jsonify({"investigation": investigation.to_dict(include_messages=True, include_events=True)})


@ghost_bp.route("/ghost/investigations/<int:investigation_id>/messages", methods=["POST"])
@jwt_required()
def send_investigation_message(investigation_id):
    admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    data = request.get_json() or {}
    question_id = data.get("question_id")
    text = data.get("message") or ""
    if question_id and not text.strip():
        question = db.session.get(InvestigationQuestion, int(question_id))
        if not question:
            return jsonify({"error": "Question not found"}), 404
        text = question.text
    try:
        message = gi.send_admin_message(investigation, admin, text, question_id=question_id)
    except gi.InvestigationError as exc:
        return _error(exc)
    return jsonify({"message": message.to_dict()}), 201


@ghost_bp.route("/ghost/investigations/<int:investigation_id>/pause", methods=["POST"])
@jwt_required()
def pause_investigation(investigation_id):
    admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    try:
        gi.pause(investigation, admin)
    except gi.InvestigationError as exc:
        return _error(exc)
    return jsonify({"investigation": investigation.to_dict()})


@ghost_bp.route("/ghost/investigations/<int:investigation_id>/resume", methods=["POST"])
@jwt_required()
def resume_investigation(investigation_id):
    admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    try:
        gi.resume(investigation, admin)
    except gi.InvestigationError as exc:
        return _error(exc)
    return jsonify({"investigation": investigation.to_dict()})


@ghost_bp.route("/ghost/investigations/<int:investigation_id>/terminate", methods=["POST"])
@jwt_required()
def terminate_investigation(investigation_id):
    admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    data = request.get_json() or {}
    confirmation = _require_confirmation(data, "terminate this investigation")
    if confirmation:
        return confirmation
    try:
        gi.terminate(investigation, admin, (data.get("reason") or "").strip()[:500])
    except gi.InvestigationError as exc:
        return _error(exc)
    return jsonify({"investigation": investigation.to_dict()})


@ghost_bp.route("/ghost/investigations/<int:investigation_id>/suspend-user", methods=["POST"])
@jwt_required()
def suspend_investigated_user(investigation_id):
    admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    data = request.get_json() or {}
    confirmation = _require_confirmation(data, "suspend this user")
    if confirmation:
        return confirmation
    try:
        gi.suspend_user(investigation, admin, (data.get("reason") or "").strip()[:500])
    except gi.InvestigationError as exc:
        return _error(exc)
    return jsonify({"investigation": investigation.to_dict()})


@ghost_bp.route("/ghost/users/<int:user_id>/reinstate", methods=["POST"])
@jwt_required()
def reinstate_suspended_user(user_id):
    admin, error = _require_admin()
    if error:
        return error
    data = request.get_json() or {}
    confirmation = _require_confirmation(data, "reinstate this user")
    if confirmation:
        return confirmation
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404
    try:
        gi.reinstate_user(target, admin, (data.get("reason") or "").strip()[:500])
    except gi.InvestigationError as exc:
        return _error(exc)
    return jsonify({"user": target.to_dict()})


@ghost_bp.route("/ghost/investigations/<int:investigation_id>/report", methods=["GET"])
@jwt_required()
def export_investigation_report(investigation_id):
    admin, investigation, error = _admin_and_investigation(investigation_id)
    if error:
        return error
    report = gi.build_report(investigation, admin)
    filename = f"secureai-{gi.resource_code(investigation).lower()}-report"
    if (request.args.get("format") or "json").lower() == "csv":
        return Response(
            gi.report_to_csv(report),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )
    response = jsonify(report)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}.json"'
    return response


# ── investigation questions (customisable) ──────────────────────────────────

@ghost_bp.route("/ghost/questions", methods=["GET"])
@jwt_required()
def list_investigation_questions():
    _admin, error = _require_admin()
    if error:
        return error
    questions = InvestigationQuestion.query.order_by(InvestigationQuestion.is_default.desc(), InvestigationQuestion.id.asc()).all()
    return jsonify({"questions": [q.to_dict() for q in questions]})


@ghost_bp.route("/ghost/questions", methods=["POST"])
@jwt_required()
def create_investigation_question():
    admin, error = _require_admin()
    if error:
        return error
    text = ((request.get_json() or {}).get("text") or "").strip()
    if not text or len(text) > 500:
        return jsonify({"error": "Question text is required (max 500 characters)"}), 400
    from app.services.ghost_persona import check_admin_message

    ok, reason = check_admin_message(text)
    if not ok:
        return jsonify({"error": reason}), 422
    question = InvestigationQuestion(text=text, created_by_id=admin.id, is_default=False)
    db.session.add(question)
    db.session.commit()
    return jsonify({"question": question.to_dict()}), 201


@ghost_bp.route("/ghost/questions/<int:question_id>", methods=["PUT", "DELETE"])
@jwt_required()
def modify_investigation_question(question_id):
    _admin, error = _require_admin()
    if error:
        return error
    question = db.session.get(InvestigationQuestion, question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404
    if request.method == "DELETE":
        db.session.delete(question)
        db.session.commit()
        return jsonify({"status": "deleted"})
    text = ((request.get_json() or {}).get("text") or "").strip()
    if not text or len(text) > 500:
        return jsonify({"error": "Question text is required (max 500 characters)"}), 400
    question.text = text
    db.session.commit()
    return jsonify({"question": question.to_dict()})
