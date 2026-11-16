# 3. Roles, Permissions & User Provisioning

## Overview
SecureAI separates **roles** (what job a person has) from **permissions** (what that role may do with governed AI and data). Permissions are data-driven: the governance engine and route guards ask "does this role hold permission X?" instead of comparing role names. Administrators provision every account on the **User Access** page (`/user-access`); public registration is disabled.

## Who can use it
Admin (provisioning). The permission model applies to everyone.

## Tech stack
| Concern | Technology |
|---|---|
| Role / permission catalog | Pure-Python tables in `services/roles.py`, `services/permissions.py` |
| Persistence | SQLAlchemy `roles`, `permissions`, role↔permission association, `users.role_id` |
| Route guards | Decorators in `utils/authz.py`: `require_role`, `require_permission`, `require_admin` |
| Login codes | `secrets` module (10-char uppercase alphanumeric) |
| Face enrolment at creation | OpenCV pipeline from [doc 2](02-face-recognition.md) |
| Frontend | `AdminCreateUserPage.jsx`, `ProtectedRoute` in `App.jsx`, `utils/roles.js` |

## How it works
**Role catalog.** 29 roles (Admin, HR, Intern, Manager, Software Engineer, Supervisor, Data Engineer, Data Analyst, Developer, QA Engineer, …) are seeded at startup. Nine of them form the governance demo set with explicit permission mappings (the same matrix is Access Control Policy §4.13):

| Permission | Guest | Intern | Software Eng. | HR | Manager | Supervisor | Data Engineer | Data Analyst | Admin |
|---|---|---|---|---|---|---|---|---|---|
| view_public_information | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| view_project_information_limited | | ✓ | | ✓ | | | | ✓ | ✓ |
| view_project_information_full | | | ✓ | | ✓ | ✓ | ✓ | | ✓ |
| view_employee_pii | | | | ✓ | ✓ | | | | ✓ |
| view_employee_salary | | | | ✓ | | | | | ✓ |
| view_warehouse_masked_data | | | | | | | ✓ | ✓ | ✓ |
| view_warehouse_raw_data | | | | | | | ✓ | | ✓ |
| use_ai_assistant | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ai_governance_admin, manage_policies, manage_risk_configuration, manage_users, system_configuration_admin | | | | | | | | | ✓ |

Any other catalog role receives a default employee set (`view_public_information`, `view_project_information_limited`, `use_ai_assistant`).

**Manager roles** (Admin, HR, Manager, Team Lead, Tech Lead, Project/Product/Operations Manager) unlock work-management administration (`is_manager_role`).

**Startup seeding** (`create_app`): `_seed_roles` → `_sync_users_to_roles` (normalises `user.role`, sets `role_id`) → `_seed_permissions` → `_seed_role_permissions`. Seeding is additive and idempotent.

**Provisioning flow** (`POST /api/admin/create-user`):
1. Admin enters username, email, role, and optionally captures a face photo.
2. The server generates a unique login code, stores its hash as the password hash, and stores the code for the admin to hand over.
3. If an image is supplied, a face embedding is built and stored as the user's `FaceProfile`.
4. The response shows the login code once; `POST /api/admin/check-user-code` lets an admin verify a username/code pair.

## Key files
- `backend/app/services/roles.py`, `services/permissions.py`, `utils/authz.py`
- `backend/app/routes/admin.py`, `routes/roles.py`, `routes/users.py`
- `frontend/src/pages/AdminCreateUserPage.jsx`, `frontend/src/utils/roles.js`, `frontend/src/App.jsx`

## API
| Method | Path | Access |
|---|---|---|
| POST | `/api/admin/create-user` | Admin |
| POST | `/api/admin/check-user-code` | Admin |
| GET | `/api/roles` | JWT |
| GET | `/api/users` | JWT: active users except self (for pickers/messaging) |

## Security
- All authorization is server-side; `ProtectedRoute adminOnly/managerOnly` only shapes the UI.
- `require_permission` returns 403 with the required permission name, which aids debugging without leaking data.
- Credentials (passwords, API keys, SSNs, …) are blocked for **every** role regardless of permission (see doc 5).

## Limitations
- The role→permission map lives in code (seeded into tables); there is no UI to edit permissions.
- No self-service password change; login codes are admin-issued.
