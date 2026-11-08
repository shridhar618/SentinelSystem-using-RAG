# 16. Private Messaging

## Overview
One-to-one real-time chat between employees (`/messages`), with online presence, typing indicators, unread counts per contact, and persisted history.

## Who can use it
Every authenticated user, with any other active user.

## Tech stack
| Concern | Technology |
|---|---|
| Real time | **Flask-SocketIO** server events + **socket.io-client** |
| History / unread | REST endpoints, SQLAlchemy `messages` |
| Frontend | `PrivateChatPage.jsx`, shared socket from `utils/socket.js` |

## How it works
```
connect  (query ?token=<JWT>) → verify JWT → join private room "user_<id>"
                               → broadcast "online_users"
private_message {token, receiver_id, content}
   → verify sender → persist Message → emit "new_message" to receiver's room
                                     → echo to sender's room
typing / stop_typing → "user_typing" / "user_stop_typing" to the receiver
disconnect → remove from presence → broadcast "online_users"
```
REST endpoints load conversation history, send messages without a socket, and drive the unread badges.

## API
| Method | Path |
|---|---|
| GET | `/api/messages/<other_id>` |
| POST | `/api/messages` |
| GET | `/api/messages/unread` |
| GET | `/api/messages/unread-by-contact` |
| GET | `/api/users` (contact list) |

## Data model
`messages` — `sender_id`, `receiver_id`, `content`, `is_read`, `timestamp`.

## Security
Rooms are joined only after JWT verification on connect, so a client cannot subscribe to another user's room. Socket events re-verify the token.

## Limitations
Presence is tracked in process memory (one socket per user id); no group chats or attachments.
