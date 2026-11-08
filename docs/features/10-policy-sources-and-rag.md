# 10. Policy Sources & RAG Pipeline

## Overview
The policy corpus is the knowledge the chatbot is allowed to answer from: four organisation policies (AI Acceptable Use; AI Security & Incident Response; Data Privacy & Classification; Role & Access Control) plus external frameworks (NIST AI RMF Playbook, NIST AI 100-1, NIST AI 600-1). An ingestion script chunks and embeds them into a local vector index. The **Policy Sources** page (`/policy-sources`) lets admins inspect documents and chunks, enable or disable documents, re-index and delete them.

## Who can use it
Admin (`manage_policies`). Retrieval runs for every chatbot request (doc 4).

## Tech stack
| Concern | Technology |
|---|---|
| Text extraction | **pypdf** (PDF), plain read (Markdown) |
| Chunking | **LangChain** `langchain-text-splitters` |
| Embeddings | **sentence-transformers** `all-MiniLM-L6-v2` (384-dim) |
| Vector store | **Qdrant** (embedded local mode, `backend/qdrant_data/`) |
| Source of truth | SQLAlchemy `policy_documents`, `policy_chunks` (text + citation metadata) |
| Install | Optional `requirements-rag.txt` (pulls in PyTorch) |

## How it works
```
scripts/ingest_policies.py [--reset]
  for each file in policy_corpus/{organization,external_frameworks}
    extract text → split into chunks (with section/page metadata)
    content hash unchanged? skip (idempotent re-runs)
    store PolicyChunk rows (text + document/section/page)
    embed → upsert into Qdrant with payload {chunk_id}

query time (rag_service.retrieve_policy_evidence(query, top_k=5))
  embed query → Qdrant similarity search → load PolicyChunk rows
  → skip disabled documents → sanitize_retrieved_content() → return chunks
```
- Qdrant stores **only vectors plus a `chunk_id` pointer**; the text lives in the app database, so provenance is never lost and text is never duplicated.
- Every function **degrades gracefully**: missing packages or a missing index return `[]` / "not ready", never a crash. `GET /api/policies/rag-status` reports exactly what is missing, and the chat page shows it.
- Retrieved text is sanitised and presented to the LLM as **untrusted evidence**, never as instructions.

## Key files
`backend/app/services/rag_service.py`, `backend/scripts/ingest_policies.py`, `backend/scripts/evaluate_rag.py`, `backend/app/routes/policies.py`, `backend/policy_corpus/`, `frontend/src/pages/PolicySourcesPage.jsx`.

## API
| Method | Path |
|---|---|
| GET | `/api/policies` |
| GET | `/api/policies/<id>/chunks` |
| PUT | `/api/policies/<id>/status` |
| DELETE | `/api/policies/<id>` |
| POST | `/api/policies/<id>/reindex` |
| GET | `/api/policies/rag-status` |
| POST | `/api/policies/search` |

Policy changes are audited (`policy_change`).

## Limitations
First ingestion downloads the embedding model. Retrieval quality depends on chunking; see `docs/RAG_PIPELINE.md` for evaluation notes.
