# Phase 17 — KPI / Workload: Implementation Notes

## Starting point

Confirmed by reading the routes (not assuming): `work_management.py` only had a **per-assignment** KPI endpoint (`GET /work/assignments/<id>/kpi`). No aggregate, workforce-wide metrics existed anywhere — the brief's explicit Phase 17 asks (Assigned/Completed/Pending tasks, Completion rate, Workload, Overdue tasks) had no endpoint to serve them from.

## What was added

**`backend/app/routes/work_management.py`** — `GET /work/workload`, plus a `_workload_summary_for_user()` helper. Role-appropriate visibility as the brief asks: a regular employee gets only their own summary; a manager/admin can additionally pass `?scope=team` for every assignee's numbers, or `?user_id=<id>` for one specific person.

**`frontend/src/pages/WorkloadPage.jsx`** (new) — stat cards for the current user's own metrics, plus a team breakdown table for managers/admins. Registered at `/workload`, open to all authenticated users (like `/my-work`), and added to the sidebar's Workforce section for everyone.

## Every metric traces to a real, existing convention — none invented

I deliberately reused definitions that already exist elsewhere in the codebase rather than inventing new ones:
- **"Overdue"** uses the *exact* same condition as `_compute_capacity_risk()` (due date in the past, status not completed) — so this new page and the existing capacity-risk system can never disagree about what counts as overdue.
- **"Workload"** = count of currently non-completed assignments — the same signal `_compute_capacity_risk()` already uses internally to flag an assignee with "many active incomplete assignments," now surfaced as a number in its own right instead of only a side effect of a risk calculation.
- **"Completion rate"** = completed ÷ total, the most literal, explainable definition — not a KPI-weighted average, which would be harder to justify to someone looking at the number.

This matters given the brief's explicit "avoid meaningless fake KPIs" instruction — every number here is either a direct count or a ratio of direct counts from real `WorkAssignment` rows, and where a definition already existed in the codebase, this reuses it exactly rather than introducing a second, possibly-conflicting definition of "overdue" or "workload."

## Verified for real

Extracted the aggregation logic verbatim and ran it in Python against realistic fixture data:
- A mixed set of 7 assignments (2 completed, 2 in-progress, 3 pending/draft/todo, 2 overdue) — all 6 derived numbers came out correct, including completion rate as an exact fraction
- **A completed task with a wildly past due date is correctly never counted as overdue** — this is the one case worth double-checking in overdue logic, since a naive "due_date < today" check without the status guard would wrongly flag finished work
- **Empty workload (a new hire with zero assignments)** doesn't divide by zero and returns an honest `0.0` completion rate rather than crashing or returning `null`

Also verified every icon used in the new page is already proven to work elsewhere in the codebase, and syntax-checked all modified/new files with esbuild.

## What I could NOT verify

The actual database queries: whether `WorkAssignment.query.filter_by(assigned_to_user_id=user.id).all()` and the team-scope join return correct results against real data, and whether the role-based access checks (`_is_admin_or_hr`) correctly gate `?user_id=` requests for a non-manager trying to view someone else's workload. Same sandbox constraint as every phase touching the database.

**Please verify:**
```bash
cd backend && python app.py
curl http://localhost:5001/api/work/workload -H "Authorization: Bearer <employee_token>"
# should return only that employee's own numbers

curl "http://localhost:5001/api/work/workload?scope=team" -H "Authorization: Bearer <manager_token>"
# should return every assignee's summary

curl "http://localhost:5001/api/work/workload?user_id=<other_user_id>" -H "Authorization: Bearer <employee_token>"
# should be 403 -- an employee cannot view someone else's workload
```
```bash
cd frontend && npm run build && npm run dev
# visit /workload as both a regular employee and a manager
```
