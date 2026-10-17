"""
Phase 27 — surfaces SecurityEvent rows, which have existed since Phase 1
and been populated by Attack Simulation since Phase 20, but had no API
endpoint or UI anywhere to view them until now.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.models.security_event import SecurityEvent
from app.utils.authz import require_permission

security_events_bp = Blueprint("security_events", __name__)


@security_events_bp.route("/security-events", methods=["GET"])
@jwt_required()
@require_permission("ai_governance_admin")
def list_security_events():
    severity = request.args.get("severity")
    source = request.args.get("source")
    limit = min(request.args.get("limit", default=50, type=int) or 50, 200)

    query = SecurityEvent.query
    if severity:
        query = query.filter_by(severity=severity)
    if source:
        query = query.filter_by(source=source)

    events = query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()
    return jsonify({
        "events": [e.to_dict() for e in events],
        "counts": {
            "high": SecurityEvent.query.filter_by(severity="high").count(),
            "medium": SecurityEvent.query.filter_by(severity="medium").count(),
            "low": SecurityEvent.query.filter_by(severity="low").count(),
        },
    }), 200
