# Phase 23 — Error Handling: Implementation Notes

## Mostly a verification phase — much of this was already done in Phase 21

Phase 21 (Security Hardening) already added global `@app.errorhandler` coverage for 404/500/generic exceptions, ensuring the API never returns an HTML error page and never leaks a stack trace to the client while still logging the real exception server-side via `app.logger.exception()`. That work directly satisfies this phase's "backend should return structured errors," "do not expose stack traces," and "log technical errors internally" requirements — rather than redo it, this phase verified it holds and audited the frontend.

## Backend error response consistency — audited, confirmed consistent

Grepped every route file for any error response that deviates from the established `{"error": "..."}` shape. Found none — the handful of non-`error`-keyed responses that came up are all **success** confirmations (`{"message": "Signed out"}`, `{"message": "Assignment deleted"}`, etc.), a distinct and consistently-applied pattern across the entire codebase, not an inconsistency. 21+ phases of reading this codebase's routes turned up nothing to fix here.

## One real frontend gap found and fixed

Audited every pre-existing page I hadn't personally written this session for the four required states (loading/success/empty/error). Found `FaceAttendancePage.jsx` conflating three of them:

- **No loading indicator for the initial records fetch at all.** The attendance history list went straight from nothing to populated with no feedback in between — on a slow connection, a user would see the "No attendance records yet" empty-state message first, which then silently flips to real data. That's actively misleading: it tells the user something false (no records exist) while the real answer is "don't know yet, still checking."
- **A failed request was indistinguishable from zero records.** The fetch's `catch` block set the records list to `[]` on any error — meaning a network failure or a 500 rendered the exact same "No attendance records yet" message as a genuinely empty history. A user (or an admin checking team attendance) would have no way to tell "nothing happened yet" from "something broke."

Fixed both: added distinct `myRecordsLoading`/`myRecordsError` and `teamRecordsLoading`/`teamRecordsError` state, each rendering its own message — loading, error, or the genuine empty state — in that priority order, for both the personal and team attendance panels.

## What I did NOT find a need to change

Spot-checked several other pre-existing pages (`QuestionBankPage.jsx`, `WorkAssignmentsPage.jsx`, `WorkEscalationsPage.jsx`) for the same four states — all already had reasonable coverage, just under slightly different naming (`busy`, `submitting`, etc. rather than literally "loading"), which a naive grep for the word "loading" alone would have missed. `AdminCreateUserPage.jsx` has no empty state because it's purely a form with no list to be empty — correctly not a gap.

## Verified for real

Syntax-checked the modified `FaceAttendancePage.jsx` with esbuild. The loading/error/empty branching logic itself is simple enough (a priority-ordered ternary chain) that I reviewed it directly rather than extracting it for a separate test — there's no non-trivial computation here to verify beyond "does the right branch render for the right state," which is a rendering concern I can't check without a browser.

## What I could NOT verify

Whether the new loading/error states actually render correctly and in the right sequence during a real network request — that needs a browser, ideally with throttled network conditions to actually observe the loading state before data arrives (on a fast local connection, the loading state might flash too briefly to see without devtools' network throttling).

**Please verify:**
```bash
cd frontend && npm run build && npm run dev
```
Open the Attendance page, enable network throttling in devtools, and confirm you see "Loading attendance records..." before the list populates. To check the error path, temporarily stop the backend after the frontend loads and refresh — should show "Couldn't load attendance records" rather than a false "No records yet."
