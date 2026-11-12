# SecureAI — Feature Documentation

SecureAI is an **AI Governance & Accountability Platform** for an internal organisation. Every AI request passes through role-based access control, a rule-based compliance engine, risk scoring, a tamper-evident audit trail, and human-reviewed escalation. Around that core sit workforce tools (face attendance, work management, messaging) and security-lab tools (Ghost Mode, Attack Simulator).

Each document below follows the same structure: **Overview → Who can use it → Tech stack → How it works → Key files → API → Data model → Security → Configuration → Limitations.**

## Feature index

| # | Feature | Audience | Doc |
|---|---|---|---|
| 1 | Authentication & Sessions | Everyone | [01-authentication.md](01-authentication.md) |
| 2 | Face Unlock & Face Attendance | Everyone (enrolment: Admin/HR) | [02-face-recognition.md](02-face-recognition.md) |
| 3 | Roles, Permissions & User Provisioning | Admin | [03-rbac-and-user-provisioning.md](03-rbac-and-user-provisioning.md) |
| 4 | AI Governance Chatbot | Roles with `use_ai_assistant` | [04-ai-governance-chatbot.md](04-ai-governance-chatbot.md) |
| 5 | Governance Engine, Compliance Check & Risk Configuration | Engine (all), config (Admin) | [05-governance-engine.md](05-governance-engine.md) |
| 6 | Risk Tracking & Governance Cases | Admin | [06-governance-cases.md](06-governance-cases.md) |
| 7 | Alert Center (Notifications) | Everyone | [07-alert-center.md](07-alert-center.md) |
| 8 | Audit Logging, Admin Dashboard & Security Events | Admin | [08-audit-and-admin-dashboard.md](08-audit-and-admin-dashboard.md) |
| 9 | Blockchain Explorer (tamper-evident audit chain) | Admin | [09-blockchain-explorer.md](09-blockchain-explorer.md) |
| 10 | Policy Sources & RAG Pipeline | Admin | [10-policy-sources-and-rag.md](10-policy-sources-and-rag.md) |
| 11 | Users & Logins (user management, login history) | Admin | [11-user-management.md](11-user-management.md) |
| 12 | Ghost Mode (Honeypot + Interactive Investigations) | Admin | [12-ghost-mode.md](12-ghost-mode.md) |
| 13 | Attack Simulator | Admin | [13-attack-simulator.md](13-attack-simulator.md) |
| 14 | Work Management (assignments, KPI, board, escalations) | Managers / employees | [14-work-management.md](14-work-management.md) |
| 15 | Projects & AI-drafted Tasks | Managers | [15-projects-and-ai-tasks.md](15-projects-and-ai-tasks.md) |
| 16 | Private Messaging | Everyone | [16-private-messaging.md](16-private-messaging.md) |
| 17 | Employee Self-Service Dashboard | Everyone | [17-employee-dashboard.md](17-employee-dashboard.md) |
| 18 | UI Shell, Theming & Motion | Everyone | [18-ui-shell.md](18-ui-shell.md) |

## Platform tech stack (shared by every feature)

### Backend
| Layer | Technology | Used for |
|---|---|---|
| Language | Python 3.11+ | All server code |
| Web framework | **Flask 3** (app factory, blueprints) | REST API under `/api` |
| ORM / DB | **Flask-SQLAlchemy 3 / SQLAlchemy 2**, **SQLite** (default) | Persistence; Postgres-compatible via `DATABASE_URL` |
| Auth | **Flask-JWT-Extended** | Stateless bearer tokens (8 h default expiry) |
| Real time | **Flask-SocketIO 5** + `simple-websocket` / `eventlet` | Live alerts, messaging, Ghost Mode |
| Password hashing | **Werkzeug** security helpers | PBKDF2 password / login-code hashes |
| CORS | **Flask-CORS** | Restricts API to configured origins |
| LLM providers | **Google Gemini** (`google-generativeai`), **OpenAI**, **Ollama** (local, e.g. `gemma3:4b`) | Phrasing answers; selected by `AI_PROVIDER` |
| Numerics | **NumPy** | Face-embedding maths |
| Computer vision | **OpenCV (contrib)** — YuNet DNN / Haar cascade, **Pillow** | Face detection + LBPH embeddings |
| Documents | **pypdf** | PDF text extraction (policies) |
| Optional RAG | **LangChain text splitters**, **sentence-transformers** (`all-MiniLM-L6-v2`), **Qdrant** (local) | Policy retrieval |
| Testing | **pytest** | 151 backend tests |

### Frontend
| Layer | Technology | Used for |
|---|---|---|
| Framework | **React 18** + **Vite 5** | SPA, dev server on :3000 proxying `/api` and `/socket.io` |
| Routing | **React Router 6** | Protected and admin/manager-only routes |
| Styling | **Tailwind CSS 3** with CSS-variable design tokens | Light/dark theming |
| Animation | **Framer Motion 11** | Page, list, and state transitions |
| HTTP | **Axios** (shared instance with 401 → login redirect) | API calls |
| Real time | **socket.io-client 4** | Live updates |
| Charts | **Recharts** | Dashboards |
| Drag & drop | **@dnd-kit** | Kanban board |
| Misc | **lucide-react** (icons), **date-fns**, **react-hot-toast** | UI |

### Cross-cutting conventions
- **Every API route requires a JWT** except login (and the disabled register endpoint). Authorization is enforced **server-side**; the UI only hides what a role cannot use.
- **Audit everything:** chat requests, logins, admin actions and config changes all land in one `audit_logs` table, which is hash-chained (see doc 9).
- **Schema evolution** uses idempotent `_ensure_*` helpers in `backend/app/__init__.py` (no migration framework); new tables are created by `db.create_all()` on startup.
- **Graceful degradation:** missing LLM keys, RAG packages, or a face model never crash the app; features report "setup required".

See also: [`../ARCHITECTURE.md`](../ARCHITECTURE.md), [`../API_DOCUMENTATION.md`](../API_DOCUMENTATION.md), [`../DATABASE_SCHEMA.md`](../DATABASE_SCHEMA.md), [`../RISK_ENGINE.md`](../RISK_ENGINE.md), [`../RAG_PIPELINE.md`](../RAG_PIPELINE.md).
