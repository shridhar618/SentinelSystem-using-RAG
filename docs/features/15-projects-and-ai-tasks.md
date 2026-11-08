# 15. Projects & AI-Drafted Tasks

## Overview
**Projects** group work assignments and members. Managers create projects, manage membership, and can ingest a batch of **AI-generated task drafts** (for example produced by an AI planning agent from a spec or GitHub issues). The drafts are stored with status `draft` and only become live work after a manager **approves** them. This is a human-in-the-loop pattern consistent with the rest of the platform.

## Who can use it
Managers (`is_manager_role`) manage projects and approve drafts. Members see their projects.

## Tech stack
Flask blueprints `routes/projects.py` and `routes/ai_tasks.py`; SQLAlchemy `projects`, `project_members` (many-to-many), `work_assignments`; audit rows for AI task ingestion. Frontend: `ProjectManagementModal.jsx` inside the work-assignments workspace.

## How it works
1. **Create/update** a project (`POST`/`PATCH /api/projects`); **add/remove members**. Only active users can be added.
2. **Ingest drafts:** `POST /api/projects/<id>/tasks/ai-generate` takes a list of tasks (`title`, `description`, `assigned_to_user_id`, `expected_units`, `weight`, `due_date`, `github_issue_id`, `github_branch`). Each one is validated: title required, numeric units > 0, weight ≥ 0, `YYYY-MM-DD` dates, active assignee. Valid tasks are stored as `WorkAssignment(status="draft")`, and the ingestion is audited.
3. **Review:** `GET /api/projects/<id>/tasks/pending` lists the drafts.
4. **Approve:** `POST /api/projects/<id>/tasks/approve` takes an explicit list of draft task IDs (`[ids]` or `{task_ids: [...]}`) and promotes them to `todo`, so they appear on boards and in KPIs (doc 14).

## API
| Method | Path |
|---|---|
| GET / POST | `/api/projects` |
| PATCH | `/api/projects/<id>` |
| POST | `/api/projects/<id>/members` |
| DELETE | `/api/projects/<id>/members/<user_id>` |
| POST | `/api/projects/<id>/tasks/ai-generate` |
| GET | `/api/projects/<id>/tasks/pending` |
| POST | `/api/projects/<id>/tasks/approve` |

## Limitations
The endpoint ingests already-generated task JSON; the model that drafts the tasks is external to this route. GitHub fields are stored as references only (no GitHub API sync).
