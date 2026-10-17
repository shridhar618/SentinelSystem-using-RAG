"""
Phase 28 — employee dashboard summary.

Everything here is scoped to the requesting user only, and deliberately
omits internal governance details (triggered rule names, validator notes,
risk weights, thresholds): an employee should understand *what happened and
what to do next*, not how to engineer a request around the rules.
"""

from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_

from app import db
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.governance_case import GovernanceCase
from app.models.message import Message
from app.models.risk_event import RiskEvent
from app.services.governance import DEFAULT_RISK_CONFIG
from app.services.risk_config_service import load_risk_config
from app.utils.authz import get_current_user

me_bp = Blueprint("me", __name__)

_STATUS_TO_DECISION = {"allowed": "ALLOWED", "filtered": "WARNING", "blocked": "RESTRICTED"}


def risk_indicator(cumulative_score: float, case_threshold: float) -> dict:
    """Simple LOW/MEDIUM/HIGH indicator for the employee's own view.

    Expressed as progress toward the admin-review threshold, so the label
    means something concrete ("you're approaching the point where an
    administrator will review your activity") without exposing the
    threshold value or any scoring weights.
    """
    if case_threshold <= 0:
        return {"level": "LOW", "progress": 0.0}
    progress = max(0.0, min(cumulative_score / case_threshold, 1.0))
    if progress < 0.34:
        level = "LOW"
    elif progress < 0.67:
        level = "MEDIUM"
    else:
        level = "HIGH"
    return {"level": level, "progress": round(progress, 2)}


_RISK_EXPLANATIONS = {
    "LOW": "Your recent AI usage is within policy. No action needed.",
    "MEDIUM": "Some of your recent requests were flagged. Repeated flagged requests may lead to an administrator review.",
    "HIGH": "Your recent requests have been flagged several times. An administrator may review your activity.",
}


@me_bp.route("/me/summary", methods=["GET"])
@jwt_required()
def my_summary():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    ai_filter = (AuditLog.user_id == user.id) & or_(AuditLog.event_type.is_(None), AuditLog.event_type == "ai_request")

    total_requests = AuditLog.query.filter(ai_filter).count()
    week_ago = datetime.now(UTC) - timedelta(days=7)
    week_requests = AuditLog.query.filter(ai_filter, AuditLog.timestamp >= week_ago).count()
    warnings = AuditLog.query.filter(ai_filter, AuditLog.status == "filtered").count()
    restricted_requests = AuditLog.query.filter(ai_filter, AuditLog.status == "blocked").count()

    recent = AuditLog.query.filter(ai_filter).order_by(AuditLog.timestamp.desc()).limit(5).all()
    recent_decisions = [{
        "id": log.id,
        "request": (log.query or "")[:140],
        "decision": _STATUS_TO_DECISION.get(log.status, (log.status or "").upper()),
        "risk_level": (log.risk_level or "low").upper(),
        "recommended_action": log.recommended_action,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
    } for log in recent]

    last_event = RiskEvent.query.filter_by(user_id=user.id).order_by(RiskEvent.created_at.desc()).first()
    cumulative = last_event.cumulative_score if last_event else 0.0
    config = load_risk_config()
    indicator = risk_indicator(cumulative, config.get("cumulative_risk_case_threshold", DEFAULT_RISK_CONFIG["cumulative_risk_case_threshold"]))

    restriction = GovernanceCase.query.filter_by(user_id=user.id, status="restricted").first()
    unresolved_case = GovernanceCase.query.filter(
        GovernanceCase.user_id == user.id, GovernanceCase.status != "resolved"
    ).first()

    # Tasks -- reuse the Phase 17 aggregation so numbers match the Workload page exactly.
    from app.routes.work_management import _workload_summary_for_user
    workload = _workload_summary_for_user(user)

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    today_attendance = (
        AttendanceRecord.query
        .filter(AttendanceRecord.user_id == user.id, AttendanceRecord.created_at >= today_start)
        .order_by(AttendanceRecord.created_at.desc()).first()
    )

    unread = Message.query.filter_by(receiver_id=user.id, is_read=False).count()

    return jsonify({
        "ai_usage": {
            "total_requests": total_requests,
            "last_7_days": week_requests,
            "warnings": warnings,
            "restricted_requests": restricted_requests,
        },
        "risk": {**indicator, "explanation": _RISK_EXPLANATIONS[indicator["level"]]},
        "access": {
            "restricted": restriction is not None,
            "case_code": restriction.case_code() if restriction else None,
            "under_review": unresolved_case is not None,
        },
        "recent_decisions": recent_decisions,
        "tasks": {
            "assigned": workload["assigned_tasks"],
            "completed": workload["completed_tasks"],
            "pending": workload["pending_tasks"],
            "overdue": workload["overdue_tasks"],
        },
        "attendance": {
            "today_status": today_attendance.event_type if today_attendance else None,
            "last_event_at": today_attendance.created_at.isoformat() if today_attendance and today_attendance.created_at else None,
        },
        "messages": {"unread": unread},
    }), 200
