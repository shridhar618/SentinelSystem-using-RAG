"""
Interactive Ghost Mode: investigation workflow service.

    Suspicious activity (routes/chat.py)
      -> threat detection           (services/threat_detection.py)
      -> ThreatAlert + admin alert  (record_threat_alert: existing Notification
                                     + SecurityEvent + Socket.IO admin_room,
                                     plus the existing honeytrap trap_triggered)
      -> Ghost Mode activation      (activate_investigation)
      -> controlled decoy           (handle_suspect_message: chat requests from
                                     the target are diverted here, never to
                                     RAG/LLM-with-policies/production data)
      -> AI Persona / Admin Manual  (switch_mode / send_admin_message)
      -> live monitoring            (admin_room socket events)
      -> evidence                   (ghost_investigation_* tables + report)
      -> admin action               (pause/resume/terminate/suspend_user)

Every administrator action is written to the investigation timeline AND to
the existing tamper-evident audit log.
"""

import csv
import hashlib
import io
import json
import os
from datetime import UTC, datetime, timedelta

from app import db, socketio
from app.models.ghost_investigation import (
    OPEN_INVESTIGATION_STATUSES,
    GhostInvestigation,
    GhostInvestigationEvent,
    GhostMessage,
    ThreatAlert,
)
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.ghost_persona import check_admin_message, generate_persona_reply
from app.services.notifications import emit_pending, notify_admins
from app.services.threat_detection import (
    CATEGORY_LABELS,
    ThreatAssessment,
    analyze_message,
    load_alert_threshold,
    score_to_level,
)

ADMIN_ROOM = "admin_room"
SUSPECT_REPLY_EVENT = "assistant_reply"  # deliberately neutral name
NOTIFY_COOLDOWN_MINUTES = 5
COMMON_WORD_USERNAMES = {"admin", "user", "test", "root", "guest", "demo", "staff"}


class InvestigationError(Exception):
    def __init__(self, message, status=400, code=None, extra=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.extra = extra or {}


# ── time / config helpers ────────────────────────────────────────────────────

def _now():
    return datetime.now(UTC)


def _aware(value):
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def idle_timeout():
    return timedelta(minutes=_env_float("GHOST_INVESTIGATION_IDLE_MINUTES", 120))


def max_lifetime():
    return timedelta(hours=_env_float("GHOST_INVESTIGATION_MAX_HOURS", 24))


def admin_control_lease():
    return timedelta(minutes=_env_float("GHOST_ADMIN_CONTROL_LEASE_MINUTES", 15))


def resource_code(investigation):
    return f"GHOST-{investigation.id:03d}"


# ── emit helpers (never let a socket failure break the workflow) ─────────────

def _emit(event, payload, room):
    try:
        socketio.emit(event, payload, to=room)
    except Exception as exc:  # pragma: no cover - transport failure
        print(f"[ghost-investigation] emit {event} failed: {exc}")


def emit_investigation_update(investigation):
    _emit("ghost_investigation_updated", investigation.to_dict(), ADMIN_ROOM)


def _emit_message(investigation, message):
    if investigation.status == "paused" and message.sender_type == "suspect":
        # Monitoring paused: evidence is still persisted, but not streamed live.
        return
    _emit(
        "ghost_investigation_message",
        {"investigation_id": investigation.id, "message": message.to_dict()},
        ADMIN_ROOM,
    )


def _deliver_to_suspect(investigation, message):
    _emit(
        SUSPECT_REPLY_EVENT,
        {
            "id": message.id,
            "content": message.content,
            "timestamp": message.to_dict()["created_at"],
        },
        f"user_{investigation.target_user_id}",
    )


# ── timeline / audit ─────────────────────────────────────────────────────────

def add_event(investigation, event_type, actor=None, description="", details=None):
    event = GhostInvestigationEvent(
        investigation_id=investigation.id,
        event_type=event_type,
        actor_id=actor.id if actor else None,
        description=description,
        details_json=json.dumps(details) if details else None,
    )
    db.session.add(event)
    return event


def _emit_event(investigation, event):
    _emit("ghost_investigation_event", {"investigation_id": investigation.id, "event": event.to_dict()}, ADMIN_ROOM)


def _audit(admin, investigation, action, description, metadata=None, risk_level="medium"):
    record_audit_event(
        "ghost_investigation",
        user=admin,
        description=description,
        resource=resource_code(investigation),
        status="allowed",
        risk_level=risk_level,
        reason=f"Ghost Mode action: {action}",
        metadata={"action": action, "investigation_id": investigation.id,
                  "target_user_id": investigation.target_user_id, **(metadata or {})},
        commit=False,
    )


def _touch(investigation):
    now = _now()
    investigation.last_activity_at = now
    hard_stop = _aware(investigation.started_at or now) + max_lifetime()
    investigation.expires_at = min(now + idle_timeout(), hard_stop)


# ── lookup / expiry ──────────────────────────────────────────────────────────

def expire_if_stale(investigation):
    """Lazily expire an open investigation past its idle/max lifetime.
    Returns True if it was expired by this call."""
    if not investigation or investigation.status not in OPEN_INVESTIGATION_STATUSES:
        return False
    now = _now()
    expires_at = _aware(investigation.expires_at)
    hard_stop = _aware(investigation.started_at or now) + max_lifetime()
    if (expires_at and now >= expires_at) or now >= hard_stop:
        investigation.status = "expired"
        investigation.ended_at = now
        investigation.controlling_admin_id = None
        investigation.interaction_mode = "ai_persona"
        investigation.end_reason = "Session expired (inactivity or maximum duration reached)."
        event = add_event(investigation, "expired", None, investigation.end_reason)
        db.session.commit()
        _emit_event(investigation, event)
        emit_investigation_update(investigation)
        return True
    return False


def get_open_investigation_for_user(user_id):
    investigation = (
        GhostInvestigation.query
        .filter(GhostInvestigation.target_user_id == user_id,
                GhostInvestigation.status.in_(OPEN_INVESTIGATION_STATUSES))
        .order_by(GhostInvestigation.id.desc())
        .first()
    )
    if investigation and expire_if_stale(investigation):
        return None
    return investigation


def get_investigation_or_404(investigation_id):
    investigation = db.session.get(GhostInvestigation, investigation_id)
    if not investigation:
        raise InvestigationError("Investigation not found", 404)
    expire_if_stale(investigation)
    return investigation


def _require_open(investigation):
    if investigation.status not in OPEN_INVESTIGATION_STATUSES:
        raise InvestigationError(f"Investigation is {investigation.status}; no further interaction is possible.", 409, "investigation_closed")


# ── threat alerts ────────────────────────────────────────────────────────────

def record_threat_alert(user, message, assessment: ThreatAssessment, source="ai_chat", audit_log_id=None):
    """Create a ThreatAlert when `assessment` crosses the configured
    threshold, notify admins (persisted Notification + live socket), and log
    a SecurityEvent. Returns the alert, or None if under threshold."""
    threshold = load_alert_threshold()
    if assessment.score < threshold:
        return None

    alert = ThreatAlert(
        user_id=user.id,
        message=message[:4000],
        threat_score=assessment.score,
        threat_level=assessment.level,
        category=assessment.category,
        categories_json=json.dumps(assessment.categories),
        signals_json=json.dumps(assessment.signals),
        source=source,
        audit_log_id=audit_log_id,
    )
    db.session.add(alert)
    db.session.flush()

    db.session.add(SecurityEvent(
        event_type="ghost_threat_alert",
        severity="high" if assessment.level in ("high", "critical") else "medium",
        source="ghost_mode",
        target_user_id=user.id,
        description=f"Threat detected ({assessment.level}, {assessment.score}/100): {assessment.category_label}",
        metadata_json=json.dumps({"alert_id": alert.id, "categories": assessment.categories, "threshold": threshold}),
    ))

    # Throttle admin notifications per user so a burst of probes doesn't
    # flood the alert center, unless the threat level escalates.
    cutoff = _now() - timedelta(minutes=NOTIFY_COOLDOWN_MINUTES)
    recent = (
        ThreatAlert.query
        .filter(ThreatAlert.user_id == user.id, ThreatAlert.id != alert.id, ThreatAlert.created_at >= cutoff)
        .order_by(ThreatAlert.threat_score.desc())
        .first()
    )
    should_notify = recent is None or assessment.score > (recent.threat_score or 0)

    notifications = []
    if should_notify:
        snippet = message if len(message) <= 140 else message[:137] + "..."
        notifications = notify_admins(
            "ghost_threat_alert",
            f"Threat alert · {assessment.level.upper()} {assessment.score}/100 · {user.username} · "
            f"{assessment.category_label}: “{snippet}”",
            related_alert_id=alert.id,
            commit=False,
        )
    db.session.commit()
    emit_pending(notifications)
    _emit("ghost_threat_alert", alert.to_dict(), ADMIN_ROOM)
    return alert


def alert_with_context(alert, limit=20):
    """Alert plus the user's recent real chatbot conversation (from the
    existing audit trail) so the admin can review it in context."""
    from app.models.audit_log import AuditLog

    rows = (
        AuditLog.query
        .filter(AuditLog.user_id == alert.user_id,
                (AuditLog.event_type.is_(None)) | (AuditLog.event_type == "ai_request"))
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    conversation = [
        {
            "audit_log_id": row.id,
            "query": row.query_text,
            "response": row.filtered_response,
            "status": row.status,
            "risk_level": row.risk_level,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "is_flagged_message": row.id == alert.audit_log_id,
        }
        for row in reversed(rows)
    ]
    open_inv = get_open_investigation_for_user(alert.user_id)
    return {
        **alert.to_dict(),
        "conversation": conversation,
        "open_investigation_id": open_inv.id if open_inv else None,
    }


def dismiss_alert(alert, admin, note=""):
    alert.status = "dismissed"
    alert.reviewed_by_id = admin.id
    record_audit_event(
        "ghost_investigation", user=admin,
        description=f"Dismissed threat alert #{alert.id} for user {alert.user.username if alert.user else alert.user_id}",
        resource=f"ALERT-{alert.id}", reason=note or "Dismissed as not malicious",
        metadata={"action": "dismiss_alert", "alert_id": alert.id}, commit=False,
    )
    db.session.commit()
    _emit("ghost_threat_alert", alert.to_dict(), ADMIN_ROOM)
    return alert


# ── activation ───────────────────────────────────────────────────────────────

def activate_investigation(admin, target, alert=None, legacy_session_id=None, mode="ai_persona"):
    if mode not in ("ai_persona", "admin_manual"):
        raise InvestigationError("mode must be 'ai_persona' or 'admin_manual'")
    if target.id == admin.id:
        raise InvestigationError("You cannot open an investigation on your own account.", 400)
    target_role = (target.role_ref.name if target.role_ref else target.role or "").lower()
    if target_role == "admin" or (target.role or "").lower() == "admin":
        raise InvestigationError("Administrator accounts cannot be placed into Ghost Mode.", 403)
    if target.is_active is False:
        raise InvestigationError("This user is already suspended.", 409)

    existing = get_open_investigation_for_user(target.id)
    if existing:
        raise InvestigationError("An investigation is already open for this user.", 409,
                                 "investigation_exists", {"investigation_id": existing.id})

    now = _now()
    seed = alert.threat_score if alert else 0
    investigation = GhostInvestigation(
        target_user_id=target.id,
        activated_by_id=admin.id,
        status="active",
        interaction_mode=mode,
        controlling_admin_id=admin.id if mode == "admin_manual" else None,
        admin_last_active_at=now if mode == "admin_manual" else None,
        threat_score=seed,
        threat_level=alert.threat_level if alert else score_to_level(seed),
        threat_category=alert.category if alert else None,
        legacy_session_id=legacy_session_id,
        started_at=now,
    )
    db.session.add(investigation)
    db.session.flush()
    _touch(investigation)

    if alert:
        alert.status = "investigating"
        alert.investigation_id = investigation.id
        alert.reviewed_by_id = admin.id

    event = add_event(
        investigation, "activated", admin,
        f"Interactive Ghost Mode activated for {target.username} in "
        f"{'AI Persona' if mode == 'ai_persona' else 'Admin Manual Control'} mode",
        {"alert_id": alert.id if alert else None, "mode": mode, "legacy_session_id": legacy_session_id},
    )
    _audit(admin, investigation, "activate", f"Activated Interactive Ghost Mode for '{target.username}'",
           {"alert_id": alert.id if alert else None, "mode": mode}, risk_level="high")
    db.session.add(SecurityEvent(
        event_type="ghost_mode_intervention", severity="high", source="ghost_mode",
        target_user_id=target.id,
        description=f"Interactive Ghost Mode investigation {resource_code(investigation)} opened by {admin.username}",
        metadata_json=json.dumps({"investigation_id": investigation.id}),
    ))
    db.session.commit()

    _link_legacy_session(investigation)
    _emit_event(investigation, event)
    emit_investigation_update(investigation)
    return investigation


def _link_legacy_session(investigation):
    """Mark the original in-memory Ghost Mode session (if any) so the
    existing session list shows it is under interactive investigation."""
    try:
        from app.ghost_routes import ghost_sessions

        username = investigation.target_user.username
        session = ghost_sessions.get(investigation.legacy_session_id or f"ghost_{username}")
        if session is not None:
            session["investigation_id"] = investigation.id if investigation.is_open else None
            session["investigation_status"] = investigation.status
    except Exception:  # pragma: no cover
        pass


# ── suspect side ─────────────────────────────────────────────────────────────

def _forbidden_terms(target):
    terms = []
    for (username,) in db.session.query(User.username).all():
        if username and username != target.username and username.lower() not in COMMON_WORD_USERNAMES and len(username) >= 4:
            terms.append(username)
    return terms


def _decoy_history(investigation):
    return [{"sender_type": m.sender_type, "content": m.content} for m in investigation.messages]


def _persona_respond(investigation, latest_text, deliver_via_socket=False):
    reply = generate_persona_reply(
        _decoy_history(investigation), latest_text, _forbidden_terms(investigation.target_user)
    )
    message = GhostMessage(investigation_id=investigation.id, sender_type="ai_persona", content=reply["text"])
    db.session.add(message)
    events = []
    if reply.get("guarded"):
        events.append(add_event(investigation, "persona_guard", None,
                                "Decoy persona safety guard engaged", {"reason": reply.get("guard_reason")}))
    db.session.flush()
    return message, reply, events


def handle_suspect_message(investigation, user, text):
    """Called by the chat route for a user under investigation. The
    message never reaches RAG/production; it is stored as evidence, scored,
    streamed to admins, and answered by the persona unless an admin holds
    manual control. Returns a dict for the chat route."""
    assessment = analyze_message(text)
    message = GhostMessage(
        investigation_id=investigation.id,
        sender_type="suspect",
        sender_user_id=user.id,
        content=text[:4000],
        threat_score=assessment.score,
        threat_level=assessment.level,
        categories_json=json.dumps(assessment.categories),
    )
    db.session.add(message)
    _touch(investigation)
    if assessment.score > (investigation.threat_score or 0):
        investigation.threat_score = assessment.score
        investigation.threat_level = assessment.level
        investigation.threat_category = assessment.category or investigation.threat_category

    events = []
    # Admin control lease: if the controlling admin went quiet, hand the
    # conversation back to the persona instead of leaving the suspect hanging.
    if investigation.interaction_mode == "admin_manual":
        last = _aware(investigation.admin_last_active_at)
        if investigation.status == "paused" or not last or _now() - last > admin_control_lease():
            investigation.interaction_mode = "ai_persona"
            investigation.controlling_admin_id = None
            events.append(add_event(investigation, "control_lease_expired", None,
                                    "Admin control lapsed; AI Persona resumed the conversation"))
    db.session.flush()
    _emit_message(investigation, message)

    reply_message = None
    if investigation.interaction_mode == "ai_persona":
        reply_message, _reply, guard_events = _persona_respond(investigation, text)
        events.extend(guard_events)
    db.session.commit()

    for event in events:
        _emit_event(investigation, event)
    if reply_message is not None:
        _emit_message(investigation, reply_message)
    emit_investigation_update(investigation)

    return {
        "pending": reply_message is None,
        "response": reply_message.content if reply_message else "",
        "reply_cursor": reply_message.id if reply_message else message.id,
    }


def pending_replies_for_user(user_id, after_id=0):
    investigation = (
        GhostInvestigation.query
        .filter(GhostInvestigation.target_user_id == user_id,
                GhostInvestigation.status.in_(OPEN_INVESTIGATION_STATUSES))
        .order_by(GhostInvestigation.id.desc())
        .first()
    )
    if not investigation:
        return []
    rows = (
        GhostMessage.query
        .filter(GhostMessage.investigation_id == investigation.id,
                GhostMessage.id > after_id,
                GhostMessage.sender_type.in_(("ai_persona", "admin")))
        .order_by(GhostMessage.id.asc())
        .limit(20)
        .all()
    )
    return [{"id": m.id, "content": m.content, "timestamp": m.to_dict()["created_at"]} for m in rows]


# ── admin side ───────────────────────────────────────────────────────────────

def _control_is_held_by_other(investigation, admin):
    if investigation.interaction_mode != "admin_manual" or not investigation.controlling_admin_id:
        return False
    if investigation.controlling_admin_id == admin.id:
        return False
    last = _aware(investigation.admin_last_active_at)
    return bool(last and _now() - last <= admin_control_lease())


def switch_mode(investigation, admin, mode, force=False):
    _require_open(investigation)
    if mode not in ("ai_persona", "admin_manual"):
        raise InvestigationError("mode must be 'ai_persona' or 'admin_manual'")
    if investigation.status == "paused":
        raise InvestigationError("Resume monitoring before changing the interaction mode.", 409, "investigation_paused")

    held_by_other = _control_is_held_by_other(investigation, admin)
    if held_by_other and not force:
        raise InvestigationError(
            f"{investigation.controlling_admin.username} currently holds manual control. "
            "Confirm a forced takeover to proceed.", 409, "control_held",
            {"controlling_admin": investigation.controlling_admin.username},
        )

    previous_mode = investigation.interaction_mode
    previous_admin = investigation.controlling_admin.username if investigation.controlling_admin else None
    events = []
    persona_reply = None

    if mode == "admin_manual":
        investigation.interaction_mode = "admin_manual"
        investigation.controlling_admin_id = admin.id
        investigation.admin_last_active_at = _now()
        label = "control_transferred" if held_by_other else "admin_takeover"
        desc = (f"{admin.username} forcibly took over manual control from {previous_admin}"
                if held_by_other else f"{admin.username} took manual control of the decoy conversation")
        events.append(add_event(investigation, label, admin, desc, {"previous_mode": previous_mode}))
        _audit(admin, investigation, label, desc, {"previous_admin": previous_admin}, risk_level="high" if held_by_other else "medium")
    else:
        investigation.interaction_mode = "ai_persona"
        investigation.controlling_admin_id = None
        desc = f"{admin.username} handed the conversation back to the AI Persona"
        events.append(add_event(investigation, "persona_resumed", admin, desc, {"previous_mode": previous_mode}))
        _audit(admin, investigation, "switch_to_persona", desc)
        # If the suspect is waiting on an unanswered message, answer it now.
        if investigation.messages and investigation.messages[-1].sender_type == "suspect":
            persona_reply, _r, guard_events = _persona_respond(investigation, investigation.messages[-1].content)
            events.extend(guard_events)

    _touch(investigation)
    db.session.commit()
    for event in events:
        _emit_event(investigation, event)
    if persona_reply is not None:
        _emit_message(investigation, persona_reply)
        _deliver_to_suspect(investigation, persona_reply)
    emit_investigation_update(investigation)
    return investigation


def send_admin_message(investigation, admin, text, question_id=None):
    _require_open(investigation)
    text = (text or "").strip()
    if not text:
        raise InvestigationError("Message is required")
    if len(text) > 2000:
        raise InvestigationError("Message is too long (max 2000 characters)")
    if investigation.status == "paused":
        raise InvestigationError("Monitoring is paused. Resume before sending messages.", 409, "investigation_paused")
    if investigation.interaction_mode != "admin_manual":
        raise InvestigationError("Switch to Admin Manual Control before sending messages.", 409, "not_in_manual_mode")
    if investigation.controlling_admin_id != admin.id:
        raise InvestigationError("Another administrator holds manual control of this investigation.", 403, "not_controlling_admin")
    ok, reason = check_admin_message(text)
    if not ok:
        raise InvestigationError(reason, 422, "unsafe_admin_message")

    message = GhostMessage(investigation_id=investigation.id, sender_type="admin", sender_user_id=admin.id, content=text)
    db.session.add(message)
    investigation.admin_last_active_at = _now()
    _touch(investigation)
    db.session.flush()
    details = {"message_id": message.id}
    if question_id:
        details["question_id"] = question_id
    event = add_event(investigation, "admin_message", admin,
                      "Investigation question sent" if question_id else "Admin sent a message", details)
    _audit(admin, investigation, "admin_message", f"Sent decoy message as assistant to '{investigation.target_user.username}'",
           details, risk_level="low")
    db.session.commit()

    _deliver_to_suspect(investigation, message)
    _emit_message(investigation, message)
    _emit_event(investigation, event)
    emit_investigation_update(investigation)
    return message


def pause(investigation, admin):
    if investigation.status != "active":
        raise InvestigationError(f"Only an active investigation can be paused (currently {investigation.status}).", 409)
    investigation.status = "paused"
    investigation.interaction_mode = "ai_persona"
    investigation.controlling_admin_id = None
    event = add_event(investigation, "paused", admin,
                      "Monitoring paused. The suspect stays in the isolated decoy with the AI Persona; messages are still recorded.")
    _audit(admin, investigation, "pause", "Paused Ghost Mode monitoring")
    db.session.commit()
    _emit_event(investigation, event)
    emit_investigation_update(investigation)
    return investigation


def resume(investigation, admin):
    if investigation.status != "paused":
        raise InvestigationError(f"Only a paused investigation can be resumed (currently {investigation.status}).", 409)
    investigation.status = "active"
    _touch(investigation)
    event = add_event(investigation, "resumed", admin, "Monitoring resumed")
    _audit(admin, investigation, "resume", "Resumed Ghost Mode monitoring")
    db.session.commit()
    _emit_event(investigation, event)
    emit_investigation_update(investigation)
    return investigation


def terminate(investigation, admin, reason=""):
    _require_open(investigation)
    investigation.status = "terminated"
    investigation.ended_at = _now()
    investigation.ended_by_id = admin.id
    investigation.controlling_admin_id = None
    investigation.interaction_mode = "ai_persona"
    investigation.end_reason = reason or "Terminated by administrator"
    event = add_event(investigation, "terminated", admin, f"Investigation terminated: {investigation.end_reason}")
    _audit(admin, investigation, "terminate", f"Terminated Ghost Mode investigation for '{investigation.target_user.username}'",
           {"reason": investigation.end_reason}, risk_level="high")
    db.session.commit()
    _link_legacy_session(investigation)
    _emit_event(investigation, event)
    emit_investigation_update(investigation)
    return investigation


def suspend_user(investigation, admin, reason=""):
    target = investigation.target_user
    if target.is_active is False:
        raise InvestigationError("User is already suspended.", 409)
    reason = reason or "Suspended following Ghost Mode investigation"
    target.is_active = False
    investigation.user_suspended = True
    events = [add_event(investigation, "user_suspended", admin, f"User {target.username} suspended: {reason}")]
    if investigation.is_open:
        investigation.status = "terminated"
        investigation.ended_at = _now()
        investigation.ended_by_id = admin.id
        investigation.controlling_admin_id = None
        investigation.interaction_mode = "ai_persona"
        investigation.end_reason = f"User suspended: {reason}"
        events.append(add_event(investigation, "terminated", admin, "Investigation closed because the user was suspended"))
    _audit(admin, investigation, "suspend_user", f"Suspended user '{target.username}' from Ghost Mode",
           {"reason": reason}, risk_level="high")
    db.session.add(SecurityEvent(
        event_type="ghost_mode_intervention", severity="high", source="ghost_mode", target_user_id=target.id,
        description=f"User suspended by {admin.username} via {resource_code(investigation)}",
        metadata_json=json.dumps({"investigation_id": investigation.id, "reason": reason}),
    ))
    db.session.commit()
    _link_legacy_session(investigation)
    # Drop the suspended user's live socket connection room traffic; their
    # JWT is rejected from now on (see token_in_blocklist_loader).
    _emit("session_revoked", {}, f"user_{target.id}")
    for event in events:
        _emit_event(investigation, event)
    emit_investigation_update(investigation)
    return investigation


def reinstate_user(target, admin, reason=""):
    if target.is_active is not False:
        raise InvestigationError("User is not suspended.", 409)
    target.is_active = True
    record_audit_event(
        "ghost_investigation", user=admin, description=f"Reinstated user '{target.username}'",
        resource=f"USER-{target.id}", reason=reason or "Reinstated by administrator",
        metadata={"action": "reinstate_user", "target_user_id": target.id}, commit=False,
    )
    db.session.commit()
    return target


# ── report ───────────────────────────────────────────────────────────────────

def build_report(investigation, admin):
    messages = [m.to_dict() for m in investigation.messages]
    events = [e.to_dict() for e in investigation.events]
    counts = {"suspect": 0, "ai_persona": 0, "admin": 0, "system": 0}
    category_counts = {}
    for m in investigation.messages:
        counts[m.sender_type] = counts.get(m.sender_type, 0) + 1
        for c in json.loads(m.categories_json or "[]"):
            category_counts[CATEGORY_LABELS.get(c, c)] = category_counts.get(CATEGORY_LABELS.get(c, c), 0) + 1

    body = {
        "report_type": "SecureAI Ghost Mode Investigation Report",
        "reference": resource_code(investigation),
        "generated_at": _now().isoformat(),
        "generated_by": admin.username,
        "investigation": investigation.to_dict(),
        "target": {
            "user_id": investigation.target_user_id,
            "username": investigation.target_user.username,
            "role": investigation.target_user.role,
            "account_active": investigation.target_user.is_active is not False,
        },
        "summary": {
            "suspect_messages": counts["suspect"],
            "ai_persona_messages": counts["ai_persona"],
            "admin_messages": counts["admin"],
            "peak_threat_score": investigation.threat_score,
            "peak_threat_level": investigation.threat_level,
            "primary_category": CATEGORY_LABELS.get(investigation.threat_category, investigation.threat_category),
            "category_hits": category_counts,
            "duration_seconds": investigation.duration_seconds(),
        },
        "alerts": [a.to_dict() for a in investigation.alerts],
        "transcript": messages,
        "timeline": events,
        "isolation_statement": "All suspect interactions were served from the isolated decoy environment. "
                               "No production data, credentials or student records were exposed.",
    }
    canonical = json.dumps(body, sort_keys=True, default=str)
    body["integrity_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()

    add_event(investigation, "report_exported", admin, "Investigation report exported",
              {"integrity_sha256": body["integrity_sha256"]})
    _audit(admin, investigation, "export_report", f"Exported report {resource_code(investigation)}",
           {"integrity_sha256": body["integrity_sha256"]}, risk_level="low")
    db.session.commit()
    return body


def report_to_csv(report):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["# " + report["report_type"], report["reference"]])
    writer.writerow(["# Target", report["target"]["username"], "Role", report["target"]["role"]])
    writer.writerow(["# Peak threat", report["summary"]["peak_threat_score"], report["summary"]["peak_threat_level"]])
    writer.writerow(["# Integrity SHA-256", report["integrity_sha256"]])
    writer.writerow([])
    writer.writerow(["timestamp", "kind", "actor", "content", "threat_score", "threat_level", "categories"])
    rows = []
    for m in report["transcript"]:
        actor = {"suspect": report["target"]["username"], "ai_persona": "AI Persona",
                 "admin": f"admin:{m.get('sender_username')}"}.get(m["sender_type"], m["sender_type"])
        rows.append([m["created_at"], "message", actor, m["content"], m.get("threat_score") or "",
                     m.get("threat_level") or "", ";".join(m.get("categories") or [])])
    for e in report["timeline"]:
        rows.append([e["created_at"], f"event:{e['event_type']}", e["actor"], e.get("description") or "", "", "", ""])
    rows.sort(key=lambda r: r[0] or "")
    writer.writerows(rows)
    return buffer.getvalue()
