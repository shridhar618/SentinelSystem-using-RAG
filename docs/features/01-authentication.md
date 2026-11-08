# 1. Authentication & Sessions

## Overview
Users sign in with a **username plus either a password or an admin-issued login code**. A successful login returns a JWT that the frontend stores and sends on every request. Public self-registration is disabled: accounts are created by an administrator (see [doc 3](03-rbac-and-user-provisioning.md)). Optionally, the user then completes a **Face Unlock** second step (see [doc 2](02-face-recognition.md)).

## Who can use it
Everyone. Suspended accounts are refused.

## Tech stack
| Concern | Technology |
|---|---|
| Token issuance/verification | Flask-JWT-Extended (`create_access_token`, `@jwt_required`, token blocklist loader) |
| Password / code hashing | Werkzeug `generate_password_hash` / `check_password_hash` |
| Brute-force protection | Custom in-memory sliding-window limiter (`services/rate_limit.py`) |
| Audit | `services/audit.py` → `audit_logs` table |
| Frontend session | React Context (`AuthContext.jsx`), `localStorage`, Axios default header + 401 interceptor |

## How it works
```
LoginPage ── POST /api/auth/login {username, password | login_code}
   │
   ├─ rate limit check  (5 attempts / 60 s per IP+username) ── 429
   ├─ user lookup ── 401 "Invalid credentials" (no user enumeration detail)
   ├─ verify password hash OR login code
   │     └─ failure → audit "login_failed" (medium risk) → 401
   ├─ account suspended (is_active = False)? → audit → 403
   ├─ reset limiter, create JWT (identity = user id, expires in 8 h)
   └─ audit "login" → { token, user, permissions }
```
1. `AuthContext.login()` stores the token in `localStorage` and sets `Authorization: Bearer <token>` on the shared Axios instance.
2. On reload, `AuthContext` calls `GET /api/auth/me` to rehydrate the user; if it fails, the token is discarded.
3. The Axios response interceptor (`utils/api.js`) treats any 401 (except on the login call itself) as an expired session: it clears the token and redirects to `/login`.
4. `POST /api/auth/logout` is audited. JWTs are stateless, so the client discards the token.
5. **Suspension:** a `token_in_blocklist_loader` in the app factory rejects the JWT of any user whose `is_active` is `False`, so a suspension (e.g. from Ghost Mode) takes effect on the user's very next request, not only at next login. The Socket.IO connect handler also refuses suspended users.

## Key files
- `backend/app/routes/auth.py` — register (disabled), login, logout, me, face-verify
- `backend/app/services/rate_limit.py` — limiter
- `backend/app/__init__.py` — JWT config + suspended-user token rejection
- `frontend/src/context/AuthContext.jsx`, `frontend/src/utils/api.js`, `frontend/src/pages/LoginPage.jsx`
- `frontend/src/App.jsx` — `ProtectedRoute` (`adminOnly`, `managerOnly`)

## API
| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/login` | Public. Returns `{token, user, permissions}` |
| POST | `/api/auth/register` | Always 403: registration disabled |
| POST | `/api/auth/logout` | JWT; audited |
| GET | `/api/auth/me` | JWT; current user + permissions |
| POST | `/api/auth/face-verify` | JWT; see doc 2 |

## Data model
`users` (`username`, `email`, `password_hash`, `role`, `role_id`, `login_code`, `is_active`, suspicious-user counters). Login events → `audit_logs` with `event_type` `login`, `login_failed`, `logout`.

## Security
- Generic "Invalid credentials" message for both unknown user and wrong password.
- Rate limit keyed by **(IP, username)** so an attacker can't lock a real user out from a different IP.
- Tokens expire (`JWT_ACCESS_TOKEN_EXPIRES_HOURS`, default 8).
- Startup prints a warning if `SECRET_KEY` / `JWT_SECRET_KEY` are the development defaults.
- 8 MB request body cap; JSON-only error responses (no stack traces).

## Configuration
`JWT_SECRET_KEY`, `SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_HOURS`, `CORS_ORIGINS`.

## Limitations
- The rate limiter is in-memory and per-process (use Redis/Flask-Limiter for multi-worker deployments).
- Logout does not revoke the token server-side (stateless JWT); suspension does.
