# 11. Question Bank

## Overview
A curated bank of approved questions and answers, each tagged with keywords, aliases and the roles allowed to see it. Admins manage it on the **Question Bank** page (`/question-bank`): CRUD, bulk import from JSON or PDF, CSV export, change history, and a **review queue** of user questions that had no good match. Users can favourite questions and rate answers.

## Who can use it
Admin manages. Any user can list questions for their role, favourite them and give feedback.

## Tech stack
| Concern | Technology |
|---|---|
| Storage | JSON files in `backend/app/data/` (`mock_question_bank.json`, `…_history.json`, `unanswered_questions.json`) |
| Matching | **scikit-learn** `TfidfVectorizer` (unigrams + bigrams, English stop words) + **cosine similarity**, with a keyword/alias heuristic fallback |
| Import | **pypdf** for PDFs (structured text parsing), JSON parsing |
| User data | SQLAlchemy `favorite_questions`, `question_feedback` |

## How it works
- **Matching** (`find_question_match_for_query`): builds a cached TF-IDF index over question text, aliases and keywords filtered by role, and returns the best match above a similarity threshold. Otherwise it scores keyword/alias overlap. Follow-up questions are resolved against recent conversation context (`resolve_contextual_query`).
- **Review queue:** `capture_unanswered_question()` records an unmatched query with the asker's role and username; admins mark items resolved or dismissed with a note. *Note: the current policy-RAG chat route does not call it, so the queue only fills from other callers or imported data.*
- **History:** every add, update and delete is appended with actor plus before/after snapshots.
- **Role filtering:** non-admins only see questions allowed for their role; only admins see full answers in the bank listing.

## Key files
`backend/app/services/ai_service.py` (question-bank functions), `backend/app/routes/chat.py` (`/chat/questions*`, `/chat/favorites*`, `/chat/feedback`), `frontend/src/pages/QuestionBankPage.jsx`.

## API
| Method | Path |
|---|---|
| GET/POST | `/api/chat/questions` |
| GET | `/api/chat/questions/search` |
| PUT/DELETE | `/api/chat/questions/<id>` |
| POST | `/api/chat/questions/import` |
| GET | `/api/chat/questions/export` |
| GET | `/api/chat/questions/history` |
| GET / PATCH | `/api/chat/questions/review-queue[/<id>]` |
| GET / POST / DELETE | `/api/chat/favorites[/<id>]` |
| POST | `/api/chat/feedback` |

## Limitations
File-based storage suits a single process; concurrent admin edits are last-write-wins.
