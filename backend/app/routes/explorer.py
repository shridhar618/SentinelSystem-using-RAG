"""Blockchain Explorer API: read-only views over the audit hash chain.

Admin-only, matching /api/logs, since blocks carry the same audit content.
See services/ledger.py for how blocks are sealed and verified.
"""

import re
from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, or_

from app import db
from app.models.audit_log import AuditLog
from app.services import ledger
from app.utils.authz import get_current_user

explorer_bp = Blueprint("explorer", __name__)

_HEX = re.compile(r"^[0-9a-fA-F]{4,64}$")
_MAX_PER_PAGE = 100


def _require_admin():
    user = get_current_user()
    return user if user and user.role == "admin" else None


def _seal():
    """Make sure every row is in the chain before we report on it."""
    if ledger.seal_pending(db.session.connection()):
        db.session.commit()


def _summary(log: AuditLog) -> dict:
    return {
        "seq": log.chain_seq,
        "hash": log.chain_hash,
        "prev_hash": log.chain_prev_hash,
        "log_id": log.id,
        "timestamp": ledger.iso_utc(log.timestamp),
        "username": log.username,
        "role": log.role,
        "event_type": log.event_type or "ai_request",
        "status": log.status,
        "risk_level": log.risk_level,
        "risk_score": log.risk_score,
        "is_high_risk": bool(log.is_high_risk),
        "resource": log.resource,
    }


def _sealed():
    return AuditLog.query.filter(AuditLog.chain_hash.isnot(None))


@explorer_bp.route("/explorer/stats", methods=["GET"])
@jwt_required()
def explorer_stats():
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403
    _seal()

    head = _sealed().order_by(AuditLog.chain_seq.desc()).first()
    genesis = _sealed().order_by(AuditLog.chain_seq.asc()).first()
    since = datetime.now(UTC) - timedelta(hours=24)

    by_status = dict(
        db.session.query(AuditLog.status, func.count())
        .filter(AuditLog.chain_hash.isnot(None))
        .group_by(AuditLog.status)
        .all()
    )
    by_risk = dict(
        db.session.query(AuditLog.risk_level, func.count())
        .filter(AuditLog.chain_hash.isnot(None))
        .group_by(AuditLog.risk_level)
        .all()
    )

    return jsonify({
        "height": head.chain_seq if head else 0,
        "blocks": _sealed().count(),
        "blocks_24h": _sealed().filter(AuditLog.timestamp >= since).count(),
        "high_risk": _sealed().filter(AuditLog.is_high_risk.is_(True)).count(),
        "unsealed": AuditLog.query.filter(AuditLog.chain_hash.is_(None)).count(),
        "head": _summary(head) if head else None,
        "genesis_at": ledger.iso_utc(genesis.timestamp) if genesis else None,
        "by_status": {k or "unknown": v for k, v in by_status.items()},
        "by_risk": {k or "unknown": v for k, v in by_risk.items()},
        "algorithm": "SHA-256",
        "genesis_hash": ledger.GENESIS_HASH,
    })


@explorer_bp.route("/explorer/blocks", methods=["GET"])
@jwt_required()
def explorer_blocks():
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403
    _seal()

    page = max(request.args.get("page", default=1, type=int) or 1, 1)
    per_page = min(max(request.args.get("per_page", default=20, type=int) or 20, 1), _MAX_PER_PAGE)
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    risk = request.args.get("risk_level", "").strip()
    event_type = request.args.get("event_type", "").strip()

    query = _sealed()
    if q:
        clauses = [AuditLog.username.ilike(f"%{q}%"), AuditLog.resource.ilike(f"%{q}%")]
        bare = q.lstrip("#")
        if bare.isdigit():
            clauses.append(AuditLog.chain_seq == int(bare))
        if _HEX.match(q):
            prefix = q.lower()
            clauses += [AuditLog.chain_hash.like(f"{prefix}%"), AuditLog.chain_prev_hash.like(f"{prefix}%")]
        query = query.filter(or_(*clauses))
    if status:
        query = query.filter(AuditLog.status == status)
    if risk:
        query = query.filter(AuditLog.risk_level == risk)
    if event_type:
        if event_type == "ai_request":
            query = query.filter(or_(AuditLog.event_type == "ai_request", AuditLog.event_type.is_(None)))
        else:
            query = query.filter(AuditLog.event_type == event_type)

    total = query.count()
    rows = (
        query.order_by(AuditLog.chain_seq.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    event_types = [
        row[0] or "ai_request"
        for row in db.session.query(AuditLog.event_type).distinct().all()
    ]

    return jsonify({
        "blocks": [_summary(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max((total + per_page - 1) // per_page, 1),
        "event_types": sorted(set(event_types)),
    })


@explorer_bp.route("/explorer/blocks/<int:seq>", methods=["GET"])
@jwt_required()
def explorer_block(seq):
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403
    _seal()

    log = _sealed().filter(AuditLog.chain_seq == seq).order_by(AuditLog.id).first()
    if log is None:
        return jsonify({"error": f"Block #{seq} not found"}), 404

    height = db.session.query(func.max(AuditLog.chain_seq)).scalar() or 0
    return jsonify({
        "block": _summary(log),
        "payload": log.to_dict(),
        "integrity": ledger.verify_block(db.session, seq),
        "prev_seq": seq - 1 if seq > 1 else None,
        "next_seq": seq + 1 if seq < height else None,
    })


@explorer_bp.route("/explorer/verify", methods=["GET"])
@jwt_required()
def explorer_verify():
    if not _require_admin():
        return jsonify({"error": "Admin access required"}), 403
    _seal()
    return jsonify(ledger.verify_chain(db.session))
