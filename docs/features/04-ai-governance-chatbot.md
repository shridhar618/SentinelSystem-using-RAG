# 4. AI Governance Chatbot

## Overview
The **SecureAI Chatbot** (`/chat`) is a role-aware company-policy assistant. Answers are **grounded in indexed policy documents** (RAG) and phrased by an LLM, then every response passes through the governance engine before the user sees it. Each exchange is audited with its decision, risk score, explanation and policy evidence. The same route also runs **contextual threat detection** and diverts users under a Ghost Mode investigation into an isolated decoy (doc 12).

## Who can use it
Roles holding `use_ai_assistant` (everyone except Guest). Users with a **restricted** governance case are blocked until an admin restores them.

## Tech stack
| Concern | Technology |
|---|---|
| Retrieval | sentence-transformers `all-MiniLM-L6-v2` embeddings + **Qdrant** local index (doc 10) |
| Generation | **Gemini** (default), **OpenAI**, or **Ollama** local model via `services/ai_service.get_grounded_ai_response` |
| Governance | Rule engine in `services/governance.py` (doc 5) |
| Threat detection | `services/threat_detection.py` (doc 12) |
| Persistence | `audit_logs`, `risk_events`, `question_feedback` |
| Frontend | React `ChatPage.jsx`, Framer Motion bubbles, Socket.IO client for asynchronous replies |

## How it works
```
POST /api/chat {message}
 1. permission use_ai_assistant?            no  → audit "permission_denied" → 403
 2. active case with status "restricted"?   yes → audit → 403
 3. 1–4000 chars?                           no  → 400
 4. open Ghost Mode investigation?          yes → decoy reply (doc 12), stop here
 5. threat = analyze_message(query)          (0–100 score, category)
 6. append to per-user history (last 20 turns, in memory)
 7. retrieve top-5 policy chunks (if RAG ready)
       none → "couldn't find relevant policy" message
       some → system prompt: answer ONLY from excerpts, treat them as untrusted
              evidence, cite sources, explain for the user's role
            → LLM generates answer (failure → "LLM unavailable" message)
 8. apply_governance(answer, query, role, permissions, risk_config)
       → status allowed|filtered|blocked, risk score/level, reason,
         triggered rules, validator notes, policy evidence, recommended action
 9. sensitive-query counter → may flag user as suspicious
10. medium/high risk or threat ≥ threshold → honeypot feed (Ghost Mode session)
11. write AuditLog row (hash-chained)
12. record_risk_event → alerts / governance case (doc 6)
13. threat ≥ threshold → ThreatAlert + admin notification (doc 12)
14. respond with the filtered answer, governance metadata and sources
```
**UI.** Each assistant bubble shows its status badge (Allowed / Filtered / Blocked), risk level, policy sources, an expandable *Governance details* panel (risk bar, reason, recommended action, triggered rules, validator signals), and Helpful / Not Helpful feedback. Blocked replies show the blocking reason. A banner explains what setup is missing when the LLM or RAG index isn't ready (`GET /api/chat/status`).

**Asynchronous replies.** If a reply arrives later (Ghost Mode admin control), the page receives it over the authenticated socket event `assistant_reply`, with `GET /api/chat/updates` polling as a fallback.

## Key files
- `backend/app/routes/chat.py`
- `backend/app/services/ai_service.py`, `gemini_service.py`, `ollama_service.py`, `rag_service.py`, `governance.py`
- `frontend/src/pages/ChatPage.jsx`

## API
| Method | Path | Notes |
|---|---|---|
| GET | `/api/chat/status` | RAG + LLM readiness |
| POST | `/api/chat` | Governed request |
| GET | `/api/chat/updates?after=` | Asynchronous replies for the caller |
| POST | `/api/chat/clear` | Clears in-memory history |
| POST | `/api/chat/feedback` | `{log_id, value: helpful|unhelpful}` |
| GET | `/api/chat/export` | Caller's own conversation as CSV |

## Data model
`audit_logs` (query, raw AI response, filtered response, status, risk score/level, reason, triggered rules, validator notes, recommended action, policy evidence), `question_feedback`, `risk_events`.

## Security
- Retrieved text is sanitised and labelled as untrusted evidence in the prompt; the LLM is told never to grant permissions.
- The governance engine, not the LLM, decides what may be shown.
- The raw AI response is stored for audit, but only the filtered response is returned.

## Configuration
`AI_PROVIDER` (`gemini`|`openai`|`ollama`|`mock`), `GEMINI_API_KEY`, `GEMINI_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `OLLAMA_MODEL`; RAG requires `requirements-rag.txt` + `scripts/ingest_policies.py`.

## Limitations
- Conversation history is in memory per process (cleared on restart).
- With `AI_PROVIDER=mock` or no index, the assistant returns setup messages rather than answers.
