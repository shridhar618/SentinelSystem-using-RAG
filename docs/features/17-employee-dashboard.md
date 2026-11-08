# 17. Employee Self-Service Dashboard

## Overview
**My Dashboard** (`/my-dashboard`) gives every employee a transparent view of their own AI usage and workload: request totals, warnings and blocks, their recent decisions with recommended actions, and a plain-language **risk indicator**. It shows how close they are to an admin review without exposing thresholds or scoring weights.

## Who can use it
Everyone (own data only).

## Tech stack
Flask `routes/me.py` (one aggregate endpoint), SQLAlchemy queries over `audit_logs`, `risk_events` and work assignments; React `MyDashboardPage.jsx` with Framer Motion.

## How it works
`GET /api/me/summary` returns:
- **AI usage:** total requests, allowed, warnings (filtered), blocked.
- **Recent requests:** the request (truncated to 140 characters), decision (ALLOWED/FILTERED/BLOCKED), risk level and recommended action.
- **Risk indicator:** progress = cumulative risk ÷ case threshold (capped at 1):

  | Progress | Level | Message |
  |---|---|---|
  | < 0.34 | LOW | "Your recent AI usage is within policy." |
  | < 0.67 | MEDIUM | "Some recent requests were flagged…" |
  | ≥ 0.67 | HIGH | "…an administrator may review your activity." |
- **Workload summary:** reused from work management (doc 14).

## Security
Scoped to the JWT identity; the response never includes thresholds, weights or other users' data.

## Key files
`backend/app/routes/me.py`, `frontend/src/pages/MyDashboardPage.jsx`.
