# 11. Users & Logins (Admin User Management)

## Overview
The **Users & Logins** page (`/user-management`) gives admins one place to see every account, its login history, and to manage users. It shows headline counts (total, active, inactive, suspicious users; logins and failed logins in the last 24 hours), a searchable user table, a paginated login-activity log, and a per-user detail view (recent logins, attendance, AI request counts).

## Who can use it
Admin only (page route and every API endpoint check `role == "admin"`).

## What an admin can do
| Action | Behaviour |
|---|---|
| Create | **Add user** opens the existing User Access page, because a face credential is mandatory at onboarding (`POST /api/admin/create-user`). |
| Read | User table with login counts, failed logins, last login; detail view; login activity with time, method (password / login code), IP address and browser. |
| Update | Username, email, role, active status; clear the suspicious flag. |
| Reset login code | Issues a new code shown once; the old code and password stop working. |
| Deactivate / activate | Blocks or restores sign-in without deleting anything. |
| Delete | Permanently removes the account and its personal data (face credential, attendance, notifications, answer ratings, project memberships). |

## Safety rules
- An admin cannot deactivate, demote or delete their own account, and the last active admin cannot be removed.
- Delete is refused (HTTP 409, with the blocking record counts) while the user has messages, work items, governance cases, risk events or Ghost Mode records; deactivate instead.
- Audit log rows are never deleted: they are hash-chained (see the Blockchain Explorer) and keep their username snapshot.
- Every change is written to the audit log (`admin_action`, or `role_change` for role edits).
- Login codes and password hashes are never returned by these endpoints.

## How login data is captured
`routes/auth.py` writes `login`, `login_failed` and `logout` audit events. Each event's metadata records the sign-in method, client IP (`X-Forwarded-For` aware) and User-Agent. Events recorded before this was added show no IP or browser.

## Key files
`backend/app/routes/user_management.py`, `backend/app/routes/auth.py`, `backend/tests/test_user_management.py`, `frontend/src/pages/UserManagementPage.jsx`.

## API
| Method | Path |
|---|---|
| GET | `/api/admin/users/summary` |
| GET | `/api/admin/users?q=&role=&status=` |
| GET | `/api/admin/users/<id>` |
| PUT | `/api/admin/users/<id>` |
| DELETE | `/api/admin/users/<id>` |
| POST | `/api/admin/users/<id>/reset-code` |
| GET | `/api/admin/login-activity?username=&event_type=&page=&per_page=` |
