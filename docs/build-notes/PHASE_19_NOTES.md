# Phase 19 — Ghost Mode: Implementation Notes

## A correction to my own earlier Phase 0 finding

Phase 0's audit said Ghost Mode's routes were unauthenticated. Re-checking now, properly: `app/ghost_routes.py`'s actual 6 routes **all** have `@jwt_required()`, and the admin-only ones correctly check `_is_admin()`. My original finding was likely based on the wrong file — the repo has a confusing duplicate-file structure I hadn't fully traced through before:

- `backend/ghost_routes.py` (top-level) is a harmless re-export shim: `from app.ghost_routes import ...`. The real implementation lives in `app/ghost_routes.py`.
- `backend/attack_routes.py` (top-level) is the **opposite** — it's the real implementation, and `app/attack_routes.py` is the shim that re-exports from it.

Two features, two different shim directions. Confusing, but functionally fine as long as nobody edits the wrong copy. Worth knowing for Phase 20 (Attack Simulation) too, which I'll note there.

## Two real gaps found and fixed

**1. No "terminate simulation" action existed at all.** The brief's admin checklist is "observe / send intervention message / trigger simulated restriction / terminate simulation" — Ghost Mode had the first three (`/ghost-logs`, `/ghost-admin-reply`, `/ghost-freeze`) but nothing to actually end a session. Added `POST /ghost-terminate`, following the exact same pattern (`_require_admin`, `_resolve_target_session`) as the existing freeze endpoint, and wired a "Terminate Session" button into `GhostAdminPanel.jsx` with a confirmation prompt before it fires (this fully clears session state, not just marks it inactive).

**2. Zero simulation-labeling anywhere in the UI**, despite the brief explicitly naming this as a requirement. This matters more than it might sound: the honeypot's canned fake responses are deliberately written to sound like a genuinely compromised system — *"The system backdoor is active,"* *"I found API keys in the environment variables,"* *"I can share the full user database dump."* Without any on-screen label, a screenshot of this page taken out of context could look like evidence of a real vulnerability rather than a demo. Added a persistent banner to `GhostAdminPanel.jsx`: *"SIMULATION MODE — All sessions, 'leaked' credentials, and honeypot responses below are synthetic test data."*

## A deliberate decision: no banner on the honeypot-facing side

`GhostChat.jsx` is the bait interface itself — the whole mechanism only works if it looks convincingly unrestricted to whoever is being tested. Adding a "this is fake" banner there would defeat the feature's actual purpose (catching someone who believes they've found an unrestricted AI and asks for something they shouldn't). I read the brief's "clearly label simulation mode" as applying to the **admin/operator view** — where a reviewer needs to be unambiguous that nothing here is real — not the target-facing side, where ambiguity is the point. I did not add anything to `GhostChat.jsx` and want to be explicit that this is a considered decision, not an oversight.

## What I could NOT verify

Whether `/ghost-terminate` actually clears session state correctly against a live server, whether the Socket.IO `session_terminated` event (emitted to the renamed `ghost_user_*` room from Phase 13's security fix) is received correctly by a connected client, and whether the confirmation dialog and button render correctly in a browser.

**Please verify:**
```bash
cd backend && python app.py
cd frontend && npm run dev
```
As admin, open Ghost Mode, select an active session, click "Terminate Session," confirm the prompt, and check that the session disappears from the list and a fresh interaction from that same test user starts a clean session rather than resuming old state.
