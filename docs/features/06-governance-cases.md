# 6. Risk Tracking & Governance Cases

## Overview
Risk from individual AI requests accumulates per user. A single **high-risk** request alerts admins immediately; a **pattern** of medium/high requests that crosses a configurable threshold automatically opens a **Governance Case**. Cases are reviewed by humans on the **Governance Cases** page (`/governance-cases`), where admins take recorded actions. The system never restricts anyone on its own.

## Who can use it
Admin.

## Tech stack
Flask blueprint + SQLAlchemy (`risk_events`, `governance_cases`, `admin_actions`), notifications via Socket.IO (doc 7), audit via `services/audit.py`. Frontend: React `GovernanceCasesPage.jsx` and dashboard widgets.

## How it works
```
chat request → AuditLog committed → record_risk_event(user, log, result)
   risk LOW?              → nothing tracked (routine usage is not noise)
   risk MEDIUM/HIGH       → RiskEvent row; cumulative score += risk score
   HIGH                   → notify all admins ("high_risk_request")
   cumulative ≥ threshold → GovernanceCase(status="open") if none open
     (default 1.50)          + notify admins ("governance_case_opened")
```
**Admin actions** (`POST /api/governance-cases/<id>/actions`):

| Action | Resulting case status |
|---|---|
| review | under_review |
| warn | warned |
| restrict | **restricted**: `/api/chat` now returns 403 for this user |
| restore | lifts the restriction |
| escalate | escalated |
| resolve | resolved (`resolved_at` set) |
| note | adds a note, no status change |

Every action creates an `AdminAction` row plus an audit-log entry. Case codes render as `GOV-001`. The detail view shows the risk-event timeline and the action history.

## Key files
- `backend/app/services/risk_tracking.py`
- `backend/app/routes/governance_cases.py`
- `backend/app/models/risk_event.py`, `governance_case.py`, `admin_action.py`
- `frontend/src/pages/GovernanceCasesPage.jsx`

## API
| Method | Path | Notes |
|---|---|---|
| GET | `/api/governance-cases?status=` | List |
| GET | `/api/governance-cases/<id>` | With risk events and actions |
| POST | `/api/governance-cases/<id>/actions` | `{action_type, note}` |

## Data model
- `risk_events` — user, audit log link, risk score/level, cumulative score, case link
- `governance_cases` — user, assigned admin, status (`open|under_review|warned|restricted|resolved|escalated`), trigger, risk at open, timestamps
- `admin_actions` — case, admin, action type, note

## Security
Human-in-the-loop by design: automation can open a case and alert, but only an admin action changes a user's access. Restriction is enforced server-side on the chat route.

## Limitations
Cumulative risk does not decay over time; resolving a case is the reset mechanism.
