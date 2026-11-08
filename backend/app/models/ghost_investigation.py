"""
Interactive Ghost Mode — persistent investigation storage.

The original Ghost Mode (app/ghost_routes.py) keeps its honeypot demo
sessions in memory. That remains untouched for the demo flow. These tables
add durable storage for the *interactive investigation* upgrade, so an
investigation's evidence (every suspect message, every decoy/admin reply,
every admin action) survives restarts and can be exported as a report.

Relationships:
    users 1──* ghost_threat_alerts *──1 ghost_investigations
    ghost_investigations 1──* ghost_investigation_messages
    ghost_investigations 1──* ghost_investigation_events
    notifications.related_alert_id ──> ghost_threat_alerts.id

Administrator actions are additionally written to the existing
tamper-evident audit_logs chain (services/audit.py), and the investigation
timeline lives in ghost_investigation_events.
"""

import json
from datetime import UTC, datetime

from app import db

THREAT_LEVELS = ["low", "medium", "high", "critical"]
ALERT_STATUSES = ["open", "investigating", "dismissed"]
INVESTIGATION_STATUSES = ["active", "paused", "terminated", "expired"]
OPEN_INVESTIGATION_STATUSES = ("active", "paused")
INTERACTION_MODES = ["ai_persona", "admin_manual"]
SENDER_TYPES = ["suspect", "ai_persona", "admin", "system"]


def _now():
    return datetime.now(UTC)


def _iso(value):
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _load_json(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


class ThreatAlert(db.Model):
    __tablename__ = "ghost_threat_alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    threat_score = db.Column(db.Integer, nullable=False, default=0)
    threat_level = db.Column(db.String(10), nullable=False, default="low")
    category = db.Column(db.String(40), nullable=True)
    categories_json = db.Column("categories", db.Text, nullable=True)
    signals_json = db.Column("signals", db.Text, nullable=True)
    source = db.Column(db.String(20), nullable=False, default="ai_chat")  # ai_chat | ghost_chat
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    audit_log_id = db.Column(db.Integer, db.ForeignKey("audit_logs.id"), nullable=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey("ghost_investigations.id"), nullable=True, index=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=_now, index=True)

    user = db.relationship("User", foreign_keys=[user_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
    investigation = db.relationship("GhostInvestigation", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "user_role": self.user.role if self.user else None,
            "message": self.message,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level,
            "category": self.category,
            "categories": _load_json(self.categories_json, []),
            "signals": _load_json(self.signals_json, []),
            "source": self.source,
            "status": self.status,
            "audit_log_id": self.audit_log_id,
            "investigation_id": self.investigation_id,
            "reviewed_by": self.reviewed_by.username if self.reviewed_by else None,
            "created_at": _iso(self.created_at),
        }


class GhostInvestigation(db.Model):
    __tablename__ = "ghost_investigations"

    id = db.Column(db.Integer, primary_key=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    activated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    controlling_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    ended_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    interaction_mode = db.Column(db.String(20), nullable=False, default="ai_persona")
    threat_score = db.Column(db.Integer, nullable=False, default=0)
    threat_level = db.Column(db.String(10), nullable=False, default="low")
    threat_category = db.Column(db.String(40), nullable=True)
    # Link back to the original in-memory Ghost Mode session (e.g.
    # "ghost_intern_bob") when the investigation was activated from it.
    legacy_session_id = db.Column(db.String(120), nullable=True)
    user_suspended = db.Column(db.Boolean, nullable=False, default=False)
    end_reason = db.Column(db.Text, nullable=True)

    started_at = db.Column(db.DateTime, default=_now, index=True)
    last_activity_at = db.Column(db.DateTime, default=_now)
    admin_last_active_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)

    target_user = db.relationship("User", foreign_keys=[target_user_id])
    activated_by = db.relationship("User", foreign_keys=[activated_by_id])
    controlling_admin = db.relationship("User", foreign_keys=[controlling_admin_id])
    ended_by = db.relationship("User", foreign_keys=[ended_by_id])
    alerts = db.relationship("ThreatAlert", back_populates="investigation", lazy=True)
    messages = db.relationship(
        "GhostMessage",
        backref="investigation",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="GhostMessage.id.asc()",
    )
    events = db.relationship(
        "GhostInvestigationEvent",
        backref="investigation",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="GhostInvestigationEvent.id.asc()",
    )

    @property
    def is_open(self):
        return self.status in OPEN_INVESTIGATION_STATUSES

    def duration_seconds(self):
        start = self.started_at
        end = self.ended_at or _now()
        if not start:
            return 0
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)
        return max(0, int((end - start).total_seconds()))

    def to_dict(self, include_messages=False, include_events=False):
        payload = {
            "id": self.id,
            "target_user_id": self.target_user_id,
            "target_username": self.target_user.username if self.target_user else None,
            "target_role": self.target_user.role if self.target_user else None,
            "target_active": bool(self.target_user.is_active) if self.target_user and self.target_user.is_active is not None else True,
            "activated_by": self.activated_by.username if self.activated_by else None,
            "controlling_admin": self.controlling_admin.username if self.controlling_admin else None,
            "controlling_admin_id": self.controlling_admin_id,
            "ended_by": self.ended_by.username if self.ended_by else None,
            "status": self.status,
            "interaction_mode": self.interaction_mode,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level,
            "threat_category": self.threat_category,
            "legacy_session_id": self.legacy_session_id,
            "user_suspended": self.user_suspended,
            "end_reason": self.end_reason,
            "started_at": _iso(self.started_at),
            "last_activity_at": _iso(self.last_activity_at),
            "admin_last_active_at": _iso(self.admin_last_active_at),
            "expires_at": _iso(self.expires_at),
            "ended_at": _iso(self.ended_at),
            "duration_seconds": self.duration_seconds(),
            "message_count": len(self.messages),
            "alert_ids": [alert.id for alert in self.alerts],
        }
        if include_messages:
            payload["messages"] = [message.to_dict() for message in self.messages]
        if include_events:
            payload["events"] = [event.to_dict() for event in self.events]
        return payload


class GhostMessage(db.Model):
    __tablename__ = "ghost_investigation_messages"

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey("ghost_investigations.id"), nullable=False, index=True)
    sender_type = db.Column(db.String(20), nullable=False)  # suspect | ai_persona | admin | system
    sender_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    content = db.Column(db.Text, nullable=False)
    threat_score = db.Column(db.Integer, nullable=True)
    threat_level = db.Column(db.String(10), nullable=True)
    categories_json = db.Column("categories", db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_now, index=True)

    sender = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "sender_type": self.sender_type,
            "sender_username": self.sender.username if self.sender else None,
            "content": self.content,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level,
            "categories": _load_json(self.categories_json, []),
            "created_at": _iso(self.created_at),
        }


class GhostInvestigationEvent(db.Model):
    __tablename__ = "ghost_investigation_events"

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey("ghost_investigations.id"), nullable=False, index=True)
    event_type = db.Column(db.String(40), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    description = db.Column(db.Text, nullable=True)
    details_json = db.Column("details", db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=_now, index=True)

    actor = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "event_type": self.event_type,
            "actor": self.actor.username if self.actor else "system",
            "description": self.description,
            "details": _load_json(self.details_json, {}),
            "created_at": _iso(self.created_at),
        }


class InvestigationQuestion(db.Model):
    __tablename__ = "ghost_investigation_questions"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=_now)

    created_by = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "is_default": self.is_default,
            "created_by": self.created_by.username if self.created_by else None,
            "created_at": _iso(self.created_at),
        }
