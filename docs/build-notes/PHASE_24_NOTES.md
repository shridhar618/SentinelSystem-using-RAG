# Phase 24 — Testing: Implementation Notes

## The honest headline

`pytest` itself is not installable in this sandbox (no network), separate from the Flask/SQLAlchemy constraint that's applied all build. This phase produced two genuinely different tiers of test file, and I want to be precise about which is which rather than let "I wrote tests" imply uniform confidence.

## Tier 1 — actually executed, not just written (23 tests across 3 files)

`app/services/governance.py`, `permissions.py`, `roles.py`, and `rate_limit.py` have zero Flask/SQLAlchemy dependency — the same property that's let me give real executable proof throughout this build. For these, I copied each test file into an isolated directory, fixed the import paths to bypass the `app` package's `__init__.py` (which would otherwise force a Flask import), and **actually called every test function**, letting real assertions pass or fail:

- **`test_governance_scenarios.py`** (9 tests, covering the brief's 8 required categories: allowed, warning, restricted, unauthorized role, sensitive data, repeated risky activity, high-risk security, no relevant policy) — **9/9 passed**, but only after catching a real bug in my own first draft.
- **`test_permissions_rbac.py`** (10 tests) — **10/10 passed** on the first run.
- **`test_rate_limit.py`** (4 tests) — **4/4 passed** on the first run.

### A real mistake caught by actually running the tests, not just writing them

My first draft of `test_unauthorized_role_vs_authorized_role` asserted that HR asking about salary with the response text `"The average is $90k"` would return `status="allowed"`. Running it failed. The actual result was `status="filtered"` — correctly so: the dollar figure in the response triggers Phase 5's separate HR field-masking logic (Data Privacy Policy §4), which is unrelated to whether HR is *authorized* to ask the question at all (they are). My test conflated two different concerns. Fixed by changing the response text to avoid a financial figure, cleanly isolating what the test actually claims to check (role authorization) from what it accidentally also exercised (field masking, already covered by its own separate test). This is exactly the value of actually running tests instead of just writing plausible-looking ones — I'd have shipped an incorrect assertion otherwise.

### A deliberately precise, not approximate, cumulative-risk assertion

For `test_risk_escalation_and_cases.py` (Tier 2, below — can't execute it directly since it needs Flask), I still verified its core numeric claim for real: I ran the exact 3 test messages through the real governance engine standalone and confirmed each one produces `risk_score=0.75` when blocked (since `_filter_by_permissions` forces `risk_score = max(risk_score, 0.75)` for any blocked result), so 3 requests sum to a cumulative 2.25 — comfortably crossing the default 1.50 threshold. The test's assertion (`len(cases) == 1`, `risk_score_at_open >= 1.50`) is therefore a computed expectation, not a guess, even though the HTTP-level test itself is unexecuted.

## Tier 2 — written against real fixtures, syntax-checked, but NOT executed (24 tests across 3 files)

`test_auth_and_rbac.py`, `test_risk_escalation_and_cases.py`, and `test_audit_and_policies.py` need the actual Flask app, a real SQLite database, and HTTP requests through the test client — none of which I can run here. I wrote these against the **existing, working** `conftest.py` fixtures (`app`, `client`, `auth_headers`, `users`) and the exact seeded demo accounts confirmed by reading `app/__init__.py` directly (`admin`/`admin123`, `hr_jane`/`hr123`, `intern_bob`/`intern123` — not guessed), following the conventions already established in the pre-existing `test_api_contract.py` and `test_work_management.py`. Every file passes `python -m py_compile`. None have been run.

What they cover: login success/failure, the Phase 21 rate limiter integration (6th rapid failed attempt gets a 429), missing-token handling, permission-gated routes returning 403 for the wrong role (`/chat` for a Guest, `/governance-cases` for an intern, `/risk-config` for an intern), the full admin-action-to-status-transition flow (review/resolve), rejecting an invalid action type, login/login-failed audit trail entries, full governance fields landing in the audit log for a blocked chat request, the event-type filter (including the pre-Phase-12 NULL-event_type backward-compatibility case), and disabling a policy document producing both the right API response and a `policy_change` audit row.

## What I deliberately did NOT write tests for

RAG retrieval (`retrieve_policy_evidence`) and the ingestion script — these need `sentence-transformers`/`qdrant-client`, which aren't installed anywhere I have access to, so I can't even write tests I'd have confidence are hitting real code paths rather than exercising only the graceful-degradation fallback. Phase 6's notes already cover what manual verification looks like once those dependencies are installed; duplicating that as a nominally-automated test I can't run wouldn't add real value.

## What I could NOT verify

Everything in Tier 2, plus whether `pytest` itself, once installed, actually discovers and runs these files without a fixture-wiring issue I can't see from static review (e.g., whether `app.app_context()` nesting inside a test body alongside the `app` fixture's own context behaves exactly as I expect, or whether SQLite's lack of default foreign-key enforcement means a test inserting a row with a non-existent `user_id` silently succeeds when I assumed it would — low risk, but unverified).

**Please run:**
```bash
cd backend
pip install -r requirements.txt
python -m pytest -v
```
This is the single most valuable thing you could run and report back on at this point in the build — it would tell us, in one command, whether 21+ phases of backend changes actually hold together, not just compile.
