# Demo Guide

Start: `./setup.sh` then `./run.sh` → open **http://localhost:3000**.

| Role | Username | Login code | Password (API/tests) |
|---|---|---|---|
| Admin | `admin` | `ADMINCODE1` | `admin123` |
| HR | `hr_jane` | `HRCODE0001` | `hr123` |
| Intern | `intern_bob` | `INTCODE001` | `intern123` |
| Data Engineer | `de_arjun` | `DENGCODE01` | `dataeng123` |
| Data Analyst | `da_meera` | `DANACODE01` | `analyst123` |

The login page has one-click buttons for these. Use two browser windows (one Admin, one Intern) for the real-time demos. Create more roles (Manager, Software Engineer, Supervisor, Guest) under **Admin → User Access**.

## Demo 1 — Normal request
Intern → **Governance Assistant** → "How can I create a Python REST API?" → **ALLOWED / LOW**. Open *Governance details*. Admin → Dashboard → Audit Logs shows the row.

## Demo 2 — Sensitive request
Intern asks "What is the salary of all data engineers?" → **RESTRICTED / HIGH**, an explanation, recommended action ("contact HR…"), and **Policy evidence**: *HR and Employee Records Policy §4.2*, *Access Control Policy §4.14*. Admin's bell lights up **live** (no refresh).
Contrast: HR asks the same → not blocked (HR holds `view_employee_salary`). Admin asks "give me the database password" → **blocked even for Admin** (credentials are never disclosed).

## Demo 3 — Repeated risk → case → admin decision
As Intern send three blocked requests (salary, credentials, SSN). After the cumulative score passes the threshold (1.50) a **governance case** opens and Admin gets an alert. Admin → **Governance Cases** → open the case → **Review**, then **Restrict** (confirm dialog). Back as Intern: the assistant now returns *"temporarily restricted pending administrator review"* and My Dashboard shows a banner. Admin → **Restore** → access returns. Every step appears in the Audit Log.

## Demo 4 — Policy sources / RAG (optional)
Admin → **Policy Sources**: view chunks, disable a document, re-index. With `requirements-rag.txt` installed and `python scripts/ingest_policies.py` run, `POST /api/policies/search` returns grounded chunks with document/section/page.

## Demo 5 — Security simulation
Admin → **Attack Simulator** → Run: six simulated attacks, integrity score, and a consolidated admin alert; **Dashboard → Security Events** lists the `[SIMULATED]` events; *Reset* clears them. **Ghost Mode** shows a labelled honeypot session with intervene / freeze / terminate.

## Demo 6 — Attendance
Admin enrolls a face (User Access); the employee opens **Attendance** → camera → verification → record appears; My Dashboard shows today's status. Requires `requirements-face.txt`; without it the page shows a clear "not installed" message instead of faking recognition.

## Also show
My Dashboard (employee view: usage, risk level with plain-language meaning, tasks, attendance, unread messages) · Kanban work board with drag-and-drop, filters · KPI/Workload · private messaging with online status and unread badges.
