# Phase 18 — Private Messaging: Implementation Notes

## Starting point (verified by reading, not assuming)

Confirmed **online status is already real** end-to-end — `socket_events.py` tracks connections in `_online_users` and broadcasts on connect/disconnect, and the frontend already listens and renders it. I'd have wasted effort rebuilding this had I not checked first (same lesson as Phase 16's drag-and-drop). Private conversations, message history, timestamps, and real-time delivery via Socket.IO also already worked.

## Two real gaps found

**1. Unread count existed but was unusable.** `GET /messages/unread` (a single global number) was never called from anywhere in the frontend — dead code from the UI's perspective — and there was no per-contact breakdown at all, so the conversation list had no way to show *which* contact has unread messages waiting. Added `GET /messages/unread-by-contact`, grouped by sender, and wired it into the contact list as a badge (bold name + a numeric pill), matching what any professional messaging product does.

**2. A real cross-conversation message leak.** The existing `new_message` socket handler appended *every* incoming message to whatever conversation thread happened to be open on screen, regardless of who actually sent it:
```js
socket.on('new_message', msg => {
  setMessages(prev => [...prev, msg])   // no check against the active conversation at all
})
```
If you were viewing a conversation with contact A and contact B sent you a message, B's message would incorrectly appear inside your thread with A. I found this by reading the handler while implementing unread badges — it's the same code path, so it belonged in this phase rather than filed away for later. Fixed by checking whether the incoming message actually belongs to the currently-open conversation (using a ref to avoid a stale closure, since the socket effect only re-subscribes on token change, not on every conversation switch) — if it does, it's appended to the visible thread; if it doesn't, it correctly bumps that contact's unread badge instead.

## Verified for real

Extracted the exact routing decision logic from the fixed handler and ran it in Node against three cases:
- **Bug reproduction**: a message from contact #2 while viewing a conversation with contact #1 — confirmed it does NOT leak into the open thread, and correctly increments contact #2's badge instead
- A message from the currently-open contact still appends to the visible thread with no badge bump (the correct, unchanged-feeling case)
- My own outgoing message, if echoed back via the socket, never triggers a badge on myself (checked `receiver_id === currentUserId`, not sender)

Also syntax-checked the modified files with esbuild.

## What I could NOT verify

Whether the fix actually behaves correctly with two real, concurrent browser sessions and a live Socket.IO connection — that's the only way to truly confirm a real-time race condition doesn't exist (e.g., a message arriving in the split second between switching conversations and the ref updating). The `unread-by-contact` SQL grouping query is also unverified against a real database.

**Please verify, ideally with the exact bug scenario**:
```bash
cd backend && python app.py
cd frontend && npm run dev
```
Open three browser sessions (users A, B, C). As A, open a conversation with B. Have C send A a message. **Before this fix, C's message would have appeared inside the A↔B thread — confirm it now correctly does NOT**, and that C shows an unread badge in A's contact list instead. Then click into C's conversation and confirm the badge clears.
