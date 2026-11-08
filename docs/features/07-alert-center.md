# 7. Alert Center (Notifications)

## Overview
A single service creates a **persisted notification row and pushes it live** over Socket.IO, so alerts are never shown without being stored (or stored without being pushed). The bell in the top bar lists recent alerts with an unread badge; clicking an alert deep-links to the related governance case or Ghost Mode threat alert.

## Who can use it
Every user receives their own notifications. Governance, security and threat alerts fan out to all admins.

## Tech stack
| Concern | Technology |
|---|---|
| Persistence | SQLAlchemy `notifications` |
| Live push | Flask-SocketIO, event `notification` to the private room `user_<id>` |
| Frontend | `TopBar.jsx` (socket listener + 60 s unread-count polling fallback), `DashboardPage.jsx` widget |

## How it works
```
services/notifications.py
  create_notification(user, type, message, related_case_id)   → one recipient
  notify_admins(type, message, related_case_id, related_alert_id) → every admin
  commit=False + emit_pending(): lets callers commit their own transaction
                                 first, then emit with real row ids
  _emit(): socketio.emit("notification", row.to_dict(), to="user_<id>")
           (socket failures are logged and swallowed; the row already exists)
```
**Private rooms.** On socket connect, the server verifies the JWT passed in the query string and joins `user_<id>`. Clients cannot join another user's room.

**Notification types** include `high_risk_request`, `governance_case_opened` (doc 6) and `ghost_threat_alert` (doc 12). In the bell, `related_case_id` links to `/governance-cases` ("View case →") and `related_alert_id` links to `/ghost-mode?alert=<id>` ("Investigate →").

## Key files
`backend/app/services/notifications.py`, `routes/notifications.py`, `routes/socket_events.py`, `models/notification.py`; `frontend/src/components/TopBar.jsx`, `frontend/src/utils/socket.js`.

## API
| Method | Path |
|---|---|
| GET | `/api/notifications?limit=` |
| GET | `/api/notifications/unread-count` |
| POST | `/api/notifications/<id>/read` |
| POST | `/api/notifications/read-all` |

## Data model
`notifications` — `user_id` (recipient), `type`, `message`, `related_case_id`, `related_alert_id`, `is_read`, `created_at`.

## Limitations
Single-process Socket.IO (no message queue), so multiple backend workers would need a Redis adapter.
