# RAG Pipeline (optional component)

**Status:** fully implemented as an ingestion + retrieval + evaluation toolchain, but deliberately **not wired into the live governed-chat decision path.** Authorization and risk are decided by the rule engine (see `RISK_ENGINE.md`); retrieved text is evidence for admins, never an instruction. The core app runs without any of the packages below.

## Install (optional)
```bash
cd backend
pip install -r requirements-rag.txt      # LangChain splitters/loaders, sentence-transformers (PyTorch), qdrant-client
python scripts/ingest_policies.py        # builds backend/qdrant_data/ and fills policy_documents / policy_chunks
```
`--reset` wipes and rebuilds everything. The script is idempotent: re-running replaces a document's chunks rather than duplicating them.

## Flow
```
policy_corpus/*.pdf|*.md → load (LangChain PyPDFLoader / markdown section splitter)
  → clean → chunk (RecursiveCharacterTextSplitter, 800 chars, 120 overlap)
  → embed (sentence-transformers all-MiniLM-L6-v2, 384-d)
  → Qdrant (local file-backed collection `secureai_policy_chunks`, cosine)
Query → embed → Qdrant search → PolicyChunk rows (content + document/section/page/category)
```
SQLite is the source of truth for chunk text and citation metadata; Qdrant stores vectors plus a `chunk_id` pointer.

## Corpus (`backend/policy_corpus/`)
- `external_frameworks/`: NIST AI 100-1 (AI RMF 1.0), NIST AI 600-1 (Generative AI Profile), AI RMF Playbook (supplied PDFs). **Not included:** NIST Privacy Framework, OWASP GenAI/LLM Top 10, India DPDP Act 2023. Drop the PDFs in this folder using the names in `KNOWN_DOCUMENTS` (`NIST Privacy Framework.pdf`, `OWASP GenAI Top 10.pdf`, `India DPDP Act 2023.pdf`) and re-run ingestion.
- `organization/`: the eight internal policies of Evolish Technologies Pvt. Ltd., a fictional FinTech (EV-SEC-001 to EV-SEC-008: Information Security, Data Classification and Handling, Access Control, Data Warehouse and Analytics Access, Acceptable Use of AI Tools, Data Privacy, HR and Employee Records, Incident Response and Security Monitoring). Every rule is its own numbered `## ` heading so citations are clause-level. `README.md` and the `_old/` archive of the previous four policies are not ingested. Review copies, including a single master manual in PDF and Word, are in `backend/policies_pdf/` (`scripts/export_policies_pdf.py`).

Measured while building: 7 documents chunk to ~1,300 chunks with zero extraction failures (pypdf).

## Admin tooling
`GET /api/policies`, `GET /api/policies/<id>/chunks`, `PUT /api/policies/<id>/status` (disable: excluded from retrieval, never deleted so audit evidence survives), `DELETE /api/policies/<id>`, `POST /api/policies/<id>/reindex` (503 with a clear message if the optional packages aren't installed), `POST /api/policies/search` (admin retrieval test). UI: **Policy Sources**.

## Safety rules implemented
1. Retrieved content is evidence, not instructions: the decision code never reads `PolicyChunk` (verified by grep).
2. `sanitize_retrieved_content()` neutralizes instruction-injection patterns; it must be used before any retrieved text is placed in an LLM prompt (not needed today because nothing does that).
3. Disabled documents are never returned.
4. No fabricated citations: results are real chunk rows; with no evidence the system says so.

## Evaluation
`python scripts/evaluate_rag.py` computes retrieval precision/recall (document-level) and timing against `evaluation/eval_dataset.json`. **It has not been run: no results exist yet, and none are claimed.** Answer relevance and faithfulness need human/LLM-judge review and are intentionally not auto-scored.

## Enabling RAG in chat (future step)
After confirming retrieval quality with `evaluate_rag.py`: call `retrieve_policy_evidence()` from `routes/chat.py` to *supplement* (not replace) the static citations, pass chunk text through `sanitize_retrieved_content()` before any prompt use, and keep the allow/block decision in `governance.py`.
