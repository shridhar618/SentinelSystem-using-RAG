# 14. Work Management (Assignments, KPI, Board, Workload, Escalations)

## Overview
A workforce module for assigning measurable work, tracking progress as units completed, computing KPIs, visualising work on a Kanban board, monitoring workload and capacity risk, and raising escalations (with an AI-suggested draft).

| Page | Route | Audience |
|---|---|---|
| Work Assignments workspace | `/work-assignments` | Managers |
| Work Board (Kanban) | `/work-board` | Managers |
| Work Escalations | `/work-escalations` | Managers |
| My Work | `/my-work` | Everyone (own assignments, progress updates) |
| Workload | `/workload` | Everyone |

## Tech stack
| Concern | Technology |
|---|---|
| API | Flask blueprint `routes/work_management.py` |
| Data | SQLAlchemy `work_assignments` (self-referencing `parent_id` hierarchy), `work_progress_updates`, `work_escalations`, `projects` |
| Kanban drag & drop | **@dnd-kit/core** (`KanbanBoard.jsx`) |
| Charts | **Recharts** |
| AI suggestion | `ai_service.get_ai_json_response` (configured LLM) with a deterministic fallback |
| Manager check | `services/roles.is_manager_role` |

## How it works
**Assignments** have a title, description, assignee, assigner, project, `expected_units`, `weight`, due date, status (`draft, pending, todo, in_progress, review, blocked, completed`), optional GitHub issue/branch, and an optional **parent**. This gives task trees, with cycle checks via `_validate_parent_link` and endpoints for children and the full tree.

**Progress → status.** Assignees post progress updates (units completed + note). `sync_status_from_progress()` moves a task to `in_progress` once work starts and `completed` when completed units ≥ expected. Parent tasks derive their status from their children.

**KPI** (`compute_kpi`):
```
expected_units  = own value, or the sum of the children's expected units
completion_ratio = completed / expected
weighted_score   = min(completion_ratio, 1) × weight
```

**Capacity risk** (`_compute_capacity_risk`), per assignment:
- **High:** overdue and incomplete, or due within 2 days with completion below 50%.
- **Medium:** due within 5 days with completion below 75%; **no attendance in the last 3 days** for the assignee (from face attendance, doc 2); or the assignee has 3 or more incomplete assignments.

Each risk level comes with human-readable reasons and signals.

**Board.** `GET /api/work/board` groups assignments by board status; dragging a card calls `PATCH …/status`.

**Escalations.**
1. A manager describes a problem.
2. `POST /api/work/escalations/suggest` sends the message, assignment context (KPI, due dates) and system signals to the LLM with a strict JSON-only prompt.
3. The result is normalised: severity low/medium/high, impact delay/blocked/risk, and a suggestion. If the LLM fails or returns invalid JSON, a deterministic fallback derives severity from capacity risk.
4. The manager files the escalation (`POST`) and later updates its status (`PATCH`).

## Key files
`backend/app/routes/work_management.py`, `backend/app/models/work_assignment.py`, `work_progress_update.py`, `work_escalation.py`; `frontend/src/pages/WorkAssignmentsWorkspacePage.jsx`, `WorkAssignmentsPage.jsx`, `WorkBoardPage.jsx`, `WorkEscalationsPage.jsx`, `MyWorkPage.jsx`, `WorkloadPage.jsx`, `frontend/src/components/KanbanBoard.jsx`.

## API
| Method | Path |
|---|---|
| GET / POST | `/api/work/assignments` |
| PATCH / DELETE | `/api/work/assignments/<id>` |
| PATCH | `/api/work/assignments/<id>/status` |
| POST | `/api/work/assignments/<id>/progress` |
| GET | `/api/work/assignments/<id>/children`, `/tree`, `/kpi` |
| GET | `/api/work/board` |
| GET | `/api/work/workload` |
| GET / POST | `/api/work/escalations` |
| POST | `/api/work/escalations/suggest` |
| PATCH | `/api/work/escalations/<id>` |

## Security
Managers create, assign and administer; employees see and update only their own work. Assignees must be active users.

## Limitations
Capacity-risk rules are fixed heuristics (not configurable from the UI).
