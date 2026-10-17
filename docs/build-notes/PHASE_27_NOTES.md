# Phase 27 — Admin Dashboard Polish: Implementation Notes

## A note on the sandbox reset

Partway into this phase the container reset again (same as during Phase 16). I recovered by unzipping `sentinelSystem-phase26.zip` — the last file delivered to you — confirmed Phase 26's work was intact, and re-verified tooling before continuing. The per-phase zips remain the real source of truth for this build.

## Starting point: most of this dashboard already existed

Phases 4, 11, 13, and 14 already delivered most of what the brief's Phase 27 names: Governance Overview and Risk Overview (Phase 4's stat cards and charts), AI Usage Trends (Phase 4's usage-over-time chart), Governance Cases (Phase 11's full page), Recent Audit Activity (the existing Audit Logs tab), and an alert center (Phase 13's notification bell). This phase's job was finding what was *genuinely* missing, not rebuilding what existed.

## Genuinely missing, and now added

**1. Security Events were invisible everywhere.** I grepped the entire frontend and all backend routes for `SecurityEvent`/`security_event` — **zero matches**. The model has existed since Phase 1 and Attack Simulation has been creating real rows in it since Phase 20, but there was no API endpoint and no UI anywhere that could display them. Data was being written into a table nothing could read. Added:
- `GET /security-events` (new `security_events.py` blueprint, gated by `ai_governance_admin`) with severity/source filters and per-severity counts
- A new **Security Events** tab on the Dashboard: three severity count cards, a severity filter, and an event table — with distinct loading/error/empty states (the loading-vs-empty distinction fixed in Phase 23 applied here from the start rather than retrofitted). The tab's header shows a high-severity count badge, mirroring the existing Threats tab. It's lazy-loaded: the request only fires when the tab is actually opened, rather than adding another request to every dashboard page load for a tab most visits won't open.

**2. Governance Cases and Active Alerts weren't visible from the dashboard itself.** Both existed, but only on other pages (`/governance-cases`, the TopBar bell dropdown) — an admin looking at the dashboard had to navigate away to learn whether anything needed attention. Added a compact `OverviewWidgets` component to the Overview tab: open (unresolved) cases and the 5 most recent alerts side by side, each with proper loading/error/empty states and links through to the full views. Initially I wrote the links as plain `<a href>` tags, then caught that these cause a full page reload (dropping the Socket.IO connection and in-memory state) — switched to react-router's `Link` for proper client-side navigation before shipping.

**3. Delivering on a promise from Phase 12.** That phase's notes explicitly said the backend `event_type` / `date_from` / `date_to` audit filters were built but the UI controls were deliberately deferred "to Phase 27's admin dashboard polish." Added them: an event-type dropdown (AI request, login, failed login, logout, admin action, risk config change, policy change) and a date-range picker, wired into the existing fetch/pagination/dependency-array pattern so changing a filter resets to page 1 like every other filter.

## Verified for real

- **Contract check**: the backend's `/logs` parameter names (`username`, `risk_level`, `event_type`, `date_from`, `date_to`) were grepped directly from `logs.py` and confirmed to match exactly what the frontend now sends — not trusted from memory, which has bitten me earlier in this build.
- **Date handling**, tested against the exact value format an HTML `<input type="date">` emits (`YYYY-MM-DD`): parses correctly; both selected days are fully included at their edges (first and last second); the day before and after are excluded; an inverted range (from > to) returns nothing gracefully instead of raising.
- Confirmed `RiskBadge` (reused for security-event severity) already handles `low`/`medium`/`high` exactly.
- Each edit to `DashboardPage.jsx` verified to have landed exactly once (the state, request params, dependency array), and the file syntax-checked with esbuild after every change.

## What I could NOT verify

Whether `GET /security-events` returns correct data against a real database, whether the lazy-loading tab actually triggers its fetch correctly in a running browser (the `useEffect` depending on `[activeTab, loadSecurityEvents]` is straightforward but unexercised), and whether the new filter controls fit visually in the existing filter row at narrower widths — I added two date inputs plus a dropdown to a row that was already wrapping, and I can't see the layout.

**Please verify:**
```bash
cd backend && python app.py
cd frontend && npm run dev
```
As admin: run the Attack Simulator, then open Dashboard → Security Events and confirm six `[SIMULATED]` events appear with the tab badge updating; click Clear Demo Events in the simulator and confirm they disappear. Then on the Audit Logs tab, try the event-type dropdown and a date range — in particular confirm choosing `login` shows your own login events, and that choosing `ai_request` still shows older chat rows from before Phase 12.
