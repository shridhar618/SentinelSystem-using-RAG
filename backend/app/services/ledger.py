"""Tamper-evident hash chain over the audit trail (Blockchain Explorer).

Every AuditLog row becomes a "block": it gets a sequence number, the hash
of the block before it, and its own SHA-256 hash covering its content plus
that previous hash. Changing any field of an earlier row, deleting a row,
or reordering rows therefore breaks verification from that point on.

Sealing happens in an `after_insert` mapper event, so it covers every code
path that writes an AuditLog (chat, auth, admin actions, ...) without
touching them. Rows that predate the chain, or that were inserted with raw
SQL, are picked up by `seal_pending()`, which runs at startup and before
every explorer request.

This is tamper-*evident*, not tamper-*proof*: someone with write access to
the database could recompute every hash. Anchoring the head hash somewhere
external (a signed export, a periodic notarisation) is what closes that gap.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime

from sqlalchemy import event, func, select, text, update
from sqlalchemy.orm.attributes import set_committed_value

from app.models.audit_log import AuditLog

log = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64
_PG_LOCK_KEY = 0x5EC0A1  # arbitrary constant; serialises sealing on Postgres

_table = AuditLog.__table__

# Every content column that goes into a block's hash, by database column
# name. The chain_* columns are deliberately excluded (they *are* the chain).
HASHED_COLUMNS = [
    "id",
    "user_id",
    "username",
    "role",
    "query",
    "ai_response",
    "filtered_response",
    "status",
    "risk_score",
    "risk_level",
    "reason",
    "triggered_rules",
    "validator_notes",
    "is_high_risk",
    "recommended_action",
    "policy_evidence",
    "event_type",
    "resource",
    "metadata",
    "timestamp",
]

_content_cols = [_table.c[name] for name in HASHED_COLUMNS]


# ── Hashing ────────────────────────────────────────────────────────────────

def _normalize_ts(value: datetime | None) -> str | None:
    """A stable string for a timestamp regardless of how the driver returns it.

    The ORM writes tz-aware UTC datetimes but SQLite hands them back naive;
    hashing what was *read from the database* (always naive UTC here) keeps
    sealing and verification in agreement.
    """
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value.isoformat()


def _canonical(row) -> dict:
    data = {}
    for name in HASHED_COLUMNS:
        value = row[name]
        if isinstance(value, datetime):
            value = _normalize_ts(value)
        data[name] = value
    return data


def compute_hash(row, seq: int, prev_hash: str) -> str:
    payload = json.dumps(
        {"seq": seq, "prev": prev_hash, "data": _canonical(row)},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def iso_utc(value: datetime | None) -> str | None:
    normalized = _normalize_ts(value)
    return f"{normalized}Z" if normalized else None


# ── Sealing ────────────────────────────────────────────────────────────────

def _head(connection):
    return connection.execute(
        select(_table.c.chain_seq, _table.c.chain_hash)
        .where(_table.c.chain_hash.isnot(None))
        .order_by(_table.c.chain_seq.desc())
        .limit(1)
    ).first()


def seal_pending(connection) -> dict[int, tuple[int, str, str]]:
    """Chain every unsealed row, oldest id first. Returns {id: (seq, prev, hash)}.

    Runs inside the caller's transaction, so the seal commits (or rolls
    back) together with the rows it covers.
    """
    if connection.dialect.name == "postgresql":
        connection.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": _PG_LOCK_KEY})

    pending = connection.execute(
        select(*_content_cols).where(_table.c.chain_hash.is_(None)).order_by(_table.c.id)
    ).mappings().all()
    if not pending:
        return {}

    head = _head(connection)
    seq, prev = (head.chain_seq, head.chain_hash) if head else (0, GENESIS_HASH)

    sealed = {}
    for row in pending:
        seq += 1
        block_hash = compute_hash(row, seq, prev)
        connection.execute(
            update(_table)
            .where(_table.c.id == row["id"])
            .values(chain_seq=seq, chain_prev_hash=prev, chain_hash=block_hash)
        )
        sealed[row["id"]] = (seq, prev, block_hash)
        prev = block_hash
    return sealed


@event.listens_for(AuditLog, "after_insert")
def _seal_on_insert(mapper, connection, target):
    try:
        sealed = seal_pending(connection)
    except Exception:  # never let the ledger block an audit write
        log.exception("Failed to seal audit log %s into the hash chain", target.id)
        return
    if target.id in sealed:
        seq, prev, block_hash = sealed[target.id]
        # Keep the in-session object in sync with what was written.
        set_committed_value(target, "chain_seq", seq)
        set_committed_value(target, "chain_prev_hash", prev)
        set_committed_value(target, "chain_hash", block_hash)


# ── Verification ───────────────────────────────────────────────────────────

_MAX_ISSUES = 50


def verify_chain(session) -> dict:
    """Walk the whole chain and recompute every block.

    Keeps going after the first problem (re-anchoring on the stored hash)
    so one edit doesn't hide a second, independent one further on.
    """
    started = time.perf_counter()
    issues = []
    issue_count = 0
    checked = 0
    expected_seq = 1
    prev = GENESIS_HASH

    def _flag(seq, kind, detail, expected=None, actual=None):
        nonlocal issue_count
        issue_count += 1
        if len(issues) < _MAX_ISSUES:
            issues.append({"seq": seq, "kind": kind, "detail": detail, "expected": expected, "actual": actual})

    rows = session.execute(
        select(*_content_cols, _table.c.chain_seq, _table.c.chain_prev_hash, _table.c.chain_hash)
        .where(_table.c.chain_hash.isnot(None))
        .order_by(_table.c.chain_seq, _table.c.id)
        .execution_options(yield_per=1000)
    ).mappings()

    for row in rows:
        checked += 1
        seq = row["chain_seq"]
        if seq < expected_seq:
            _flag(seq, "duplicate_sequence", "Two blocks share this sequence number (chain fork).")
        elif seq > expected_seq:
            missing = seq - expected_seq
            _flag(
                seq,
                "sequence_gap",
                f"{missing} block{'s' if missing != 1 else ''} missing before this one (deleted rows).",
                expected=str(expected_seq),
                actual=str(seq),
            )
        if row["chain_prev_hash"] != prev:
            _flag(seq, "broken_link", "Previous-hash pointer does not match the prior block.", prev, row["chain_prev_hash"])
        recomputed = compute_hash(row, seq, row["chain_prev_hash"])
        if recomputed != row["chain_hash"]:
            _flag(seq, "content_mismatch", "Block content was modified after it was sealed.", recomputed, row["chain_hash"])
        prev = row["chain_hash"]
        expected_seq = max(expected_seq, seq + 1)

    unsealed = session.execute(
        select(func.count()).select_from(_table).where(_table.c.chain_hash.is_(None))
    ).scalar_one()

    return {
        "ok": issue_count == 0,
        "checked": checked,
        "unsealed": unsealed,
        "head_hash": prev if checked else None,
        "issue_count": issue_count,
        "issues": issues,
        "first_break": issues[0] if issues else None,
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        "verified_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def verify_block(session, seq: int) -> dict | None:
    """Recompute one block and check its link to the block before it."""
    row = session.execute(
        select(*_content_cols, _table.c.chain_seq, _table.c.chain_prev_hash, _table.c.chain_hash)
        .where(_table.c.chain_seq == seq)
        .order_by(_table.c.id)
        .limit(1)
    ).mappings().first()
    if row is None:
        return None

    if seq == 1:
        expected_prev = GENESIS_HASH
    else:
        expected_prev = session.execute(
            select(_table.c.chain_hash).where(_table.c.chain_seq == seq - 1).limit(1)
        ).scalar()

    recomputed = compute_hash(row, seq, row["chain_prev_hash"])
    return {
        "hash_valid": recomputed == row["chain_hash"],
        "link_valid": expected_prev is not None and expected_prev == row["chain_prev_hash"],
        "recomputed_hash": recomputed,
        "expected_prev_hash": expected_prev,
    }
