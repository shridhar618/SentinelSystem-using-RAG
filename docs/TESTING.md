# Testing

## Backend (pytest)
```bash
cd backend
pip install -r requirements.txt
python -m pytest -v
```
Fixtures (`tests/conftest.py`): a fresh SQLite DB per test, `AI_PROVIDER=mock` (forces the offline TF-IDF path, no API keys needed), `FACE_BACKEND=test` (explicit test-only face stand-in so attendance *plumbing* is testable without dlib; never used unless set), and a rate-limiter reset. Seeded accounts used: `admin/admin123`, `hr_jane/hr123`, `intern_bob/intern123`.

| File | Tests | Covers |
|---|---|---|
| `test_governance_scenarios.py` | 9 | The 8 required scenario categories: allowed, warning (HR masking), restricted, unauthorized role, sensitive data (credentials blocked even for Admin), repeated risk (cumulative math), high-risk security, no-relevant-policy fallback |
| `test_permissions_rbac.py` | 10 | Permission catalog integrity, role→permission map, defaults for unmapped roles, name normalization |
| `test_rate_limit.py` | 4 | Limit, per-IP scoping, reset on success, case-insensitivity |
| `test_auth_and_rbac.py` | 9 | Login success/failure/429, `/me` permissions, 403s for chat (Guest), cases (Intern), risk-config (Intern) |
| `test_risk_escalation_and_cases.py` | 5 | Blocked request fields, 3 risky requests → exactly one case, admin actions/status transitions, invalid action 400 |
| `test_audit_and_policies.py` | 7 | login / login_failed audit rows, full governance fields in audit, event_type filter incl. legacy NULL rows, policy disable audited |
| existing suites | 68 | API contract, attendance, work management, projects, AI tasks, Gemini/Ollama services |

## Verification status — read this
The development environment could not install Flask/SQLAlchemy/pytest (no network), so the **full suite has not been run end-to-end by the author**. What *was* executed for real:
- The pure-Python modules (`governance`, `permissions`, `roles`, `rate_limit`) — all 23 tests in the first three files above were executed by calling each test function directly, after fixing one wrong assertion this process caught.
- Risk-engine evaluation (`scripts/evaluate_risk_engine.py`) — real numbers, see `RISK_ENGINE.md`.
- Static checks: every Python file parses; every in-project `from app.x import y` resolves; every route's auth decorator was scanned (90 routes, only login/register public); all 36 frontend files parse (esbuild); every relative import resolves; all third-party imports are declared in `requirements.txt` / `package.json`.

**First thing to do after downloading: run `python -m pytest -v` and `cd frontend && npm run build`.** If a test fails, the failure message will point at the exact line.

## Evaluation scripts
| Script | Needs | Status |
|---|---|---|
| `scripts/evaluate_risk_engine.py` | core only | **Run: 80 % decision / 86.7 % risk accuracy** on 15 scenarios |
| `scripts/evaluate_rag.py` | `requirements-rag.txt` + ingestion | **Not run — no results claimed** |

Dataset: `evaluation/eval_dataset.json` (fields: question, user_role, expected decision/risk/evidence). Two rows deliberately record the *policy-correct* answer rather than current engine output, so the evaluation exposes real gaps.

## Frontend
`npm run build` is the compile check (no unit-test runner is configured).

## CI
`.github/workflows/` runs backend tests and the frontend build on push.

## Manual end-to-end checklist
See `DEMO_GUIDE.md` — each demo doubles as an acceptance test.
