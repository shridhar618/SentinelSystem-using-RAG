# Phase 20 — Attack Simulation: Implementation Notes

## The gap flagged at the end of Phase 19, confirmed and fixed

The actually-live `attack_routes.py` (top-level file — see Phase 19's notes on the confusing shim structure) had **zero authentication** on all three routes: any anonymous request could hit `/api/attack-simulate`, `/api/attack-stop`, `/api/attack-reset`. Added `@jwt_required()` plus an admin-only check (matching Role & Access Control Policy §3.7 — governance/system administration is Admin's domain) to all three.

## A break I had to fix in the same change

Adding auth to a previously-open endpoint is only safe if every caller is updated to actually send credentials. `AttackSimulator.jsx` called all three endpoints with raw, unauthenticated `fetch()` — no `Authorization` header anywhere. Shipping the backend fix alone would have broken the feature outright for every user, including admins. Switched all three calls to the shared `api` axios wrapper (which auto-attaches the JWT, consistent with the rest of the app), and improved the error handler to surface the real backend message (e.g., "Admin access required") instead of axios's generic error text — since a 403 is now a realistic outcome that wasn't previously possible.

## A second real gap: simulated attacks never fed the actual governance pipeline

The brief's Phase 20 flow is explicit: "Security Event Created → Risk Engine → Alert → Admin Dashboard." Before this phase, `simulate_attacks()` just returned static canned JSON straight to the frontend — nothing was ever persisted. The `SecurityEvent` model has had `"attack_simulation"` as a valid `source`/`event_type` value since **Phase 1**, and nothing had ever written to it. Fixed:

- Every simulated attack now creates a real `SecurityEvent` row, clearly labeled `[SIMULATED]` in its description, with severity derived from the (still-random, still-fake) risk score — genuinely persisted, genuinely queryable from the audit/security views built in earlier phases.
- One **consolidated** admin notification per simulation run (not one per attack — six notifications for a single button click would be spam that trains admins to ignore the alert center, defeating Phase 13's purpose).
- `/attack-reset` — the brief's "Clear Demo Events" button — now actually deletes the `SecurityEvent` rows this feature created (`source="attack_simulator"`), not just a `running` flag that was never persisted anywhere in the first place.

## A deliberate scope decision: no automatic GovernanceCase

I did not wire attack-simulation events into automatic `GovernanceCase` creation. A governance case is tied to a specific user under review for their own risky *behavior* (Phase 10/11's whole model); an admin manually running a canned security demo isn't behavior to investigate — there's no real "who" to open a case against. I judged this the same way I've handled similar ambiguous mappings all build (Phase 5's caution-rule generalization, Phase 8's confidential-content scope) — a defensible, explicit decision rather than a forced fit.

## Verified for real

- Ran the exact severity-mapping logic (`"high" if risk >= 90 else "medium"`) against the boundary in both directions
- Ran the exact integrity-score formula against the simulated risk range's worst case (all attacks at risk 99 → integrity 90) and best case (all at risk 70 → integrity 93) — both sane
- Syntax-checked both the real `attack_routes.py` and its `app/` shim, and the modified `AttackSimulator.jsx`

## What I could NOT verify

Whether the SQLAlchemy writes (`SecurityEvent` creation, the reset endpoint's bulk delete) actually execute correctly against a real database, and — most importantly — whether the frontend's switch from raw `fetch` to the `api` wrapper actually restores working behavior end-to-end. This is the one most worth clicking through, since I changed both sides of a previously-broken contract at once.

**Please verify:**
```bash
cd backend && python app.py
cd frontend && npm run dev
```
As admin: open Attack Simulator, click Run — confirm it still works exactly as before (just now actually authenticated). Then check `/api/logs` or a database query for new `security_events` rows with `source='attack_simulator'`. Click Reset and confirm those rows are gone. Then, as a **non-admin** user, try hitting `/api/attack-simulate` directly (or via the UI if reachable) and confirm you get a clean 403, not a crash.
