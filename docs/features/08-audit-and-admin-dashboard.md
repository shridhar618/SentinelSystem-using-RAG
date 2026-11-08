# 8. Audit Logging, Admin Dashboard & Security Events

## Overview
All auditable activity lands in **one** `audit_logs` table: AI requests, permission denials, logins, admin actions, risk-configuration and policy changes, and Ghost Mode investigation actions. The **Admin Dashboard** (`/dashboard`) turns that trail into KPIs, charts, a filterable log table, a CSV export, suspicious-user management and a security-event feed.

## Who can use it
Admin.

## Tech stack
| Concern | Technology |
|---|---|
| Unified audit writer | `services/audit.py` (`record_audit_event`) + direct `AuditLog` rows from the chat route |
| Tamper evidence | SHA-256 hash chain sealed on insert (doc 9) |
| Aggregation | SQLAlchemy queries in `routes/logs.py` |
| CSV export | Python `csv` module |
| Charts | **Recharts** (usage over time, risk distribution) |
| Indexes | `timestamp`, `user_id`, `status`, `chain_seq`, `chain_hash` (created idempotently at startup) |

## How it works
**Audit rows.** Chat rows carry the full governance result (doc 4). Non-chat events reuse the same row shape with `event_type` set (`login`, `login_failed`, `logout`, `admin_action`, `risk_config_change`, `policy_change`, `role_change`, `user_created`, `security_event`, `ghost_investigation`, `permission_denied`), `resource` (what was acted on, e.g. `GOV-003` or `GHOST-001`) and a JSON `metadata` blob.

**Dashboard data** (`GET /api/logs/stats`): totals, allowed/filtered/blocked counts, risk distribution (low/medium/high), high-risk alerts, risky requests, usage over time, per-user breakdown, suspicious users, recent high-risk requests, open governance cases and active restrictions.

**Log table** (`GET /api/logs`): filtering and pagination; `GET /api/logs/export` downloads CSV.

**Suspicious users**: `PATCH /api/logs/suspicious/<user_id>` lets an admin clear or set the flag raised by the sensitive-query counter.

**Security events** (`GET /api/security-events`): a separate feed of system signals (`suspicious_login`, `policy_bypass_attempt`, `high_risk_request`, `attack_simulation`, `ghost_mode_intervention`, `ghost_threat_alert`, …), each with `severity` and `source` (`system`, `attack_simulator`, `ghost_mode`) so lab/demo noise is clearly separated from operational signals.

## Key files
`backend/app/services/audit.py`, `routes/logs.py`, `routes/security_events.py`, `models/audit_log.py`, `models/security_event.py`; `frontend/src/pages/DashboardPage.jsx`.

## API
| Method | Path |
|---|---|
| GET | `/api/logs` |
| GET | `/api/logs/stats` |
| GET | `/api/logs/export` |
| PATCH | `/api/logs/suspicious/<user_id>` |
| GET | `/api/security-events` |

## Limitations
Audit rows are never pruned (intentional for accountability); very large tables would need archiving.
