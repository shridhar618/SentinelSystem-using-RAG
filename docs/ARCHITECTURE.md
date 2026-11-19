# Architecture

SecureAI — an **AI Governance & Accountability Platform** for an internal organization. The core idea: general-purpose AI does not know an organization's role boundaries, so every AI request passes through RBAC → rule-based policy compliance → risk scoring → audit → human-reviewed escalation.

## Component view
```
React + Vite + Tailwind + Framer Motion  (:3000, proxies /api and /socket.io)
        │ REST (JWT in Authorization header)         │ Socket.IO (JWT in query)
        ▼                                            ▼
Flask app factory (backend/app/__init__.py)  ──  Flask-SocketIO
 ├─ routes/ (21 blueprints, 113 endpoints)  → see API_DOCUMENTATION.md
 ├─ utils/authz.py            get_current_user, require_role, require_permission
 ├─ services/
 │   ├─ governance.py         rule-based compliance + risk engine (pure Python)
 │   ├─ permissions.py        permission catalog + role→permission map (pure Python)
 │   ├─ risk_tracking.py      cumulative risk, case creation, alerts
 │   ├─ risk_config_service.py  RiskConfiguration table → engine config
 │   ├─ audit.py              unified audit events
 │   ├─ notifications.py      persist + real-time emit
 │   ├─ ai_service.py         Gemini / OpenAI / Ollama(gemma3:4b) + TF-IDF fallback
 │   ├─ rag_service.py        optional policy retrieval (Qdrant + sentence-transformers)
 │   ├─ face_attendance.py    OpenCV YuNet/Haar face detection + LBPH embeddings
 │   ├─ threat_detection.py   contextual 0–100 threat scoring (Ghost Mode)
 │   ├─ ghost_investigation.py  investigation workflow, alerts, reports
 │   ├─ ghost_persona.py      isolated decoy AI + injection/output guards
 │   ├─ ledger.py             SHA-256 hash chain over audit_logs
 │   └─ rate_limit.py         login brute-force limiter
 └─ models/ (27 tables) → see DATABASE_SCHEMA.md
SQLite (secureai.db)         Qdrant local index (optional, backend/qdrant_data/)
```

## The governed request (the critical path)
```
LOGIN ─ JWT (expires, default 8h) ─ role + permissions loaded
  → POST /api/chat
      permission use_ai_assistant?                 no → 403 + audit
      active admin Restriction (case restricted)?  yes → 403 + audit
      message ≤ 4000 chars
      retrieve policy chunks (RAG) → grounded LLM response
      apply_governance(): universal rules → permission-gated rules → role rules
                          → risk score → validator → policy evidence → recommended action
      AuditLog row (decision, risk, reason, evidence)
      record_risk_event(): cumulative score
          HIGH request      → alert admins (Socket.IO + notification row)
          cumulative ≥ 1.5  → GovernanceCase(open) + alert
  → Admin: Review / Warn / Restrict / Restore / Escalate / Resolve / Note
          (each = AdminAction + audit row; Restrict is enforced on /chat)
```
Principles: RBAC authorizes · the rule engine decides · policy documents supply evidence · the LLM only phrases answers · audit records everything · humans decide consequences.

## Modules
| Area | Backend | Frontend |
|---|---|---|
| Governance assistant | `routes/chat.py`, `services/governance.py` | `ChatPage.jsx` |
| Compliance check | `routes/compliance.py` | via API |
| Risk config | `routes/risk_config.py` | via API |
| Cases & alerts | `routes/governance_cases.py`, `routes/notifications.py` | `GovernanceCasesPage`, `TopBar` bell, Dashboard widgets |
| Audit & dashboards | `routes/logs.py`, `routes/security_events.py`, `routes/me.py` | `DashboardPage` (admin), `MyDashboardPage` (employee) |
| Policy corpus | `routes/policies.py`, `scripts/ingest_policies.py` | `PolicySourcesPage` |
| Attendance | `routes/attendance.py`, `services/face_attendance.py` | `FaceAttendancePage`, `FaceUnlockPage` |
| Tasks / KPI | `routes/work_management.py` | `WorkBoardPage`, `MyWorkPage`, `WorkloadPage`, … |
| Messaging | `routes/messages.py`, `routes/socket_events.py` | `PrivateChatPage` |
| Ghost Mode | `ghost_routes.py`, `services/threat_detection.py`, `services/ghost_investigation.py`, `services/ghost_persona.py` | `GhostModePage`, `GhostAdminPanel`, `GhostInvestigationConsole` |
| Attack simulation | `attack_routes.py` | `AttackSimPage` |
| Blockchain Explorer | `routes/explorer.py`, `services/ledger.py` | `modules/explorer/` |

## Security boundaries
- **Every API route requires a JWT** except `POST /auth/login` and `/auth/register` (disabled). Suspended accounts (`is_active = False`) have their JWT rejected on every route and cannot sign in or open a socket.
- Authorization is enforced **server-side** (`require_permission`, `require_role`, inline admin checks); the UI only hides what a role can't use.
- Socket.IO: private rooms (`user_<id>`) are joined only after JWT verification; `admin_room` (live Ghost Mode alerts and investigations) requires a verified admin JWT. The honeypot demo uses a separate `ghost_user_*` namespace carrying only synthetic data. Origins are enforced against `CORS_ORIGINS`.
- JWTs expire; the UI redirects to login on 401. Passwords hashed (werkzeug). Login rate-limited per (IP, username). 8 MB request cap. JSON-only errors, no stack traces; unhandled errors logged server-side.
- `DEBUG` is off by default; startup warns if `SECRET_KEY`/`JWT_SECRET_KEY` are defaults (`setup.sh` generates random ones).

## Ghost Mode and Attack Simulation (safety boundary)
- **Honeypot (normal Ghost Mode)** and **Attack Simulation** are admin-only simulations using canned/dummy data, banner-labelled "SIMULATION MODE"; Attack Simulation writes `[SIMULATED]` `security_events` and can clear them.
- **Interactive investigations** act on real users, so they are tightly bounded: contextual threat detection raises an alert → an admin explicitly activates (server-side confirmation) → the suspect's chatbot traffic is diverted to an **isolated decoy** that never touches RAG, the policy index or user records → AI Persona (prompt-injection and output guards) or Admin Manual Control (single controlling admin, forced takeover logged) → every action recorded in the investigation timeline and the hash-chained audit log → terminate or suspend (confirmed). Admin accounts can't be targeted; sessions expire. Details: `features/12-ghost-mode.md`.

## Frontend routes
`/login`, `/welcome`, `/my-dashboard`, `/chat`, `/policy-sources`*, `/governance-cases`*, `/dashboard`*, `/ghost-mode`*, `/attack-sim`*, `/blockchain-explorer`*, `/user-management`*, `/user-access`*, `/attendance`, `/my-work`, `/workload`, `/work-assignments`†, `/work-board`†, `/work-escalations`†, `/messages` (* admin, † manager). Sidebar sections appear only if the role has something in them.

## Deliberate simplifications (MCA-capstone scope)
SQLite instead of Postgres; no migration framework (idempotent `_ensure_*` helpers); in-memory rate limiter; single-process Socket.IO; RAG is optional and offline from the decision path.
