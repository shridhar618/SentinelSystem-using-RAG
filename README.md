# SecureAI — AI Governance & Accountability Platform

An internal organizational platform that makes AI use **role-aware, policy-checked, auditable and accountable**. MCA final-year capstone.

> Built on top of the open-source *SentinelSystem* codebase (governed chat, work management, attendance, messaging). This project adds the governance core: permissions, rule-based compliance, risk scoring, cumulative escalation, governance cases, alerts, audit, policy management, and the employee/admin dashboards.

## Problem
Organizations have employees with different roles and permissions, but general-purpose AI doesn't know those boundaries. An employee can ask it for data their role can't access, use it against policy, or repeatedly attempt risky things — and nobody is accountable.

## What SecureAI does
1. **Role-Based Access Control** — permission catalog; enforced on the server.
2. **Governance assistant** — every answer carries decision (ALLOWED / WARNING / RESTRICTED), risk, explanation, recommended action, and policy evidence.
3. **Transparent rule-based risk engine** (not ML) with admin-configurable weights/thresholds.
4. **Cumulative risk → governance case → human decision** (warn / restrict / restore / escalate / resolve). Nothing is auto-terminated.
5. **Real-time alerts** (Socket.IO), **audit log** of everything (AI requests, logins, admin actions, config/policy changes), **security events**.
6. **Policy-grounded chatbot** — retrieves active company policy passages and uses a configured LLM to answer with source references, scoped to the signed-in user's role.
7. Supporting modules: face-recognition attendance, Kanban tasks, KPI/workload, private messaging, Ghost Mode (honeypot simulation plus database-backed interactive investigations of real suspicious users, driven by contextual threat detection) and Attack Simulation (safe, labelled simulation).

**Principles:** RBAC authorizes · the rule engine decides · policy documents provide evidence · the LLM explains · audit records · humans decide consequences.

## Tech stack
Backend: Python, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-SocketIO · Frontend: React, Vite, Tailwind, Framer Motion, Recharts · DB: SQLite · AI/RAG: sentence-transformers, Qdrant, and a configured Ollama, Gemini, or OpenAI LLM · Vision: OpenCV (YuNet/Haar detection + LBPH embeddings) · Tests: pytest · CI: GitHub Actions.

## Quick start
Requires Python 3.11+ and Node 18+.
```bash
./setup.sh      # venv, core deps, npm install, backend/.env with random secrets
./run.sh        # backend :5001 + frontend :3000
```
Open **http://localhost:3000** and use the one-click demo logins (below). Manual:
```bash
cd backend && python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then set SECRET_KEY / JWT_SECRET_KEY (setup.sh does this for you)
python app.py                   # http://localhost:5001

cd frontend && npm install && npm run dev      # http://localhost:3000
```
Docker: `docker compose up --build` (frontend on :3000).

### Deploy on Render

This repository includes a Render Blueprint in [`render.yaml`](render.yaml).
It deploys the frontend and backend as one same-origin Docker web service, so
API requests and Socket.IO do not need a separate proxy or frontend service.

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint** and select the repository.
3. Confirm the generated `SECRET_KEY` and `JWT_SECRET_KEY` values, then deploy.
4. Set `AI_PROVIDER` to `gemini` and add `GEMINI_API_KEY` in the Render
   service environment if you want hosted model responses. The default
   `mock` provider keeps the deployment usable without an external AI key.

The Blueprint uses a small persistent disk for the SQLite prototype database.
For production or multiple instances, use a managed PostgreSQL database and
set `DATABASE_URL` to its connection string. Replace `CORS_ORIGINS=*` with the
exact public origin if the frontend is later split into a separate service.

### Demo accounts
| Role | Username | Login code | Password |
|---|---|---|---|
| Admin | admin | ADMINCODE1 | admin123 |
| HR | hr_jane | HRCODE0001 | hr123 |
| Intern | intern_bob | INTCODE001 | intern123 |

Demo credentials are for local use only. Create further roles (Manager, Software Engineer, Supervisor, Guest…) in **Admin → User Access**.

## Enable policy chat (RAG + LLM)

The chat requires a built policy index and a working LLM provider. From `backend/`:

```bash
source venv/bin/activate                 # Windows: venv\Scripts\activate
pip install -r requirements-rag.txt
```

Configure `AI_PROVIDER` in `backend/.env` as `gemini`, `openai`, or `ollama`, then set the matching API key (`GEMINI_API_KEY` or `OPENAI_API_KEY`) or install Ollama and pull a model (`ollama pull gemma3:4b`). Build the index against the same database used by the running app:

```bash
python scripts/ingest_policies.py
```

Restart the backend. The chatbot status shows whether the LLM and policy retrieval are ready. It will not produce policy answers from the demo question bank if either service is unavailable.

## Optional feature packs
| Pack | Install | Enables |
|---|---|---|
| RAG | Included in the policy chat setup above | Policy retrieval, ingestion, re-index, RAG evaluation |
| Face recognition | `pip install -r requirements-face.txt` | Real face enrollment/verification. `dlib` can be hard to build on Windows — see the file's header for the conda route |
| Local LLM | install [Ollama](https://ollama.com), `ollama pull gemma3:4b`, set `AI_PROVIDER=ollama` | Local Gemma-4B answers for the policy chatbot |

## Environment variables
All documented in `backend/.env.example` (every variable there is actually read by the code): `SECRET_KEY`, `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRES_HOURS`, `CORS_ORIGINS` (**must include the origin you open the app from** — Socket.IO enforces it), `DATABASE_URL`, `PORT`, `DEBUG` (keep `0`), `AI_PROVIDER` + provider keys.

## Database, tests, evaluation
- Schema: `docs/DATABASE_SCHEMA.md` (27 tables, SQLite, auto-created and auto-seeded at startup).
- Tests: `cd backend && python -m pytest -v` → see `docs/TESTING.md` (**read the verification-status section**).
- Risk-engine evaluation: `python scripts/evaluate_risk_engine.py` (run: 80 % decision / 86.7 % risk accuracy on 15 scenarios, with the 3 mismatches explained). RAG evaluation harness is included but **not yet run**.

## Documentation
`docs/features/` (per-feature docs: tech stack, how it works, API, data, security) · `docs/ARCHITECTURE.md` · `docs/API_DOCUMENTATION.md` (generated, 113 endpoints) · `docs/DATABASE_SCHEMA.md` (generated) · `docs/RISK_ENGINE.md` · `docs/RAG_PIPELINE.md` · `docs/TESTING.md` · `docs/DEMO_GUIDE.md` (6 demo workflows) · `docs/build-notes/` (phase-by-phase engineering log incl. decisions and findings) · `docs/legacy/` (superseded pre-capstone docs). Regenerate the generated docs with `python backend/scripts/generate_docs.py`.

## Honest limitations
- The original author's environment had no network, so the suite was not run end-to-end at first delivery. It has since been run: **151/151 backend tests pass** (including 32 Ghost Mode investigation tests), `npm run build` succeeds, and the app was exercised live (HTTP + Socket.IO). Live LLM/RAG answers still need a configured provider and an ingested index; see `docs/TESTING.md`.
- The rule engine has known coverage gaps (e.g. "personal addresses" phrasing isn't caught as PII; single keyword hits move the score little) — documented with evidence in `docs/RISK_ENGINE.md`.
- The policy chatbot only knows the documents present in the indexed corpus. Add approved company policies through the policy management workflow and re-index them.
- Face recognition accuracy has not been tested with a real camera.
- SQLite, in-memory login rate limiter, single-process Socket.IO — fine for a prototype, not for production scale. No migration framework.
- Attack Simulation and the Ghost Mode honeypot are simulations with dummy data only. Ghost Mode interactive investigations act on real accounts (admin-only, confirmed, audited, isolated decoy); see `docs/features/12-ghost-mode.md`.

## Future scope
Broaden/learn detection rules and add a labelled dataset; priority field on tasks; Redis-backed rate limiting and Socket.IO scaling; Postgres + Alembic; SSO; per-department policy sets.
# SentinelSystem-using-RAG
