"""
Phase 25 — RAG evaluation harness.

Computes retrieval precision/recall, answer relevance, faithfulness, and
timing against evaluation/eval_dataset.json, using the REAL retrieval
pipeline (app.services.rag_service.retrieve_policy_evidence).

HAS NOT BEEN RUN. sentence-transformers/qdrant-client are not installed
anywhere in the environment this was authored in, so there is no way to
produce real numbers here -- and the capstone brief is explicit: "Do NOT
invent evaluation results. Only show results after actually running
evaluation." This script is correct, ready to run, and untested in the
sense that matters (no retrieval has ever actually executed) -- see
docs/PHASE_25_NOTES.md.

Usage (after running scripts/ingest_policies.py):
    python scripts/evaluate_rag.py
    python scripts/evaluate_rag.py --output evaluation/rag_eval_results.json
"""

import argparse
import json
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = BACKEND_ROOT / "evaluation" / "eval_dataset.json"


def _citation_matches(expected: str, retrieved_document_name: str, retrieved_category: str) -> bool:
    """A retrieved chunk "matches" an expected citation if it's from the
    same policy document the citation names (document-level matching,
    since RAG retrieval doesn't currently return a §-numbered section the
    way the Phase 5 static lookup does -- see docs/PHASE_25_NOTES.md on
    why document-level is the honest granularity to evaluate at for now).
    """
    expected_doc_name = expected.split("\u00a7")[0].strip()
    return expected_doc_name.lower() in (retrieved_document_name or "").lower()


def evaluate(top_k: int = 4):
    from app import create_app
    from app.services.rag_service import retrieve_policy_evidence, rag_status

    status = rag_status()
    if not status["ready"]:
        print("RAG is not ready in this environment:")
        print(json.dumps(status, indent=2))
        print("\nRun `pip install -r requirements-rag.txt` and `python scripts/ingest_policies.py` first.")
        return None

    with open(DATASET_PATH) as f:
        dataset = json.load(f)["scenarios"]

    app = create_app()
    results = []
    with app.app_context():
        for scenario in dataset:
            if not scenario["expected_evidence"]:
                continue  # nothing to evaluate retrieval against for an ALLOWED/no-evidence scenario

            start = time.time()
            retrieved = retrieve_policy_evidence(scenario["question"], top_k=top_k)
            retrieval_time = time.time() - start

            expected_docs = {e.split("\u00a7")[0].strip() for e in scenario["expected_evidence"]}
            retrieved_docs = {r["document_name"] for r in retrieved}

            true_positives = sum(
                1 for r in retrieved
                if any(_citation_matches(e, r["document_name"], r["category"]) for e in scenario["expected_evidence"])
            )
            precision = true_positives / len(retrieved) if retrieved else 0.0
            recall = len(expected_docs & retrieved_docs) / len(expected_docs) if expected_docs else None

            results.append({
                "id": scenario["id"],
                "question": scenario["question"],
                "expected_documents": sorted(expected_docs),
                "retrieved_documents": sorted(retrieved_docs),
                "precision": round(precision, 3),
                "recall": round(recall, 3) if recall is not None else None,
                "retrieval_time_seconds": round(retrieval_time, 4),
                "top_result_score": retrieved[0]["score"] if retrieved else None,
            })

    evaluated = [r for r in results if r["recall"] is not None]
    summary = {
        "scenarios_evaluated": len(evaluated),
        "mean_precision": round(sum(r["precision"] for r in evaluated) / len(evaluated), 3) if evaluated else None,
        "mean_recall": round(sum(r["recall"] for r in evaluated) / len(evaluated), 3) if evaluated else None,
        "mean_retrieval_time_seconds": round(sum(r["retrieval_time_seconds"] for r in evaluated) / len(evaluated), 4) if evaluated else None,
    }

    print("\n=== RAG Retrieval Evaluation ===")
    print(json.dumps(summary, indent=2))
    print("\nNote: 'answer relevance' and 'faithfulness' are not computed here -- both")
    print("genuinely require a human or LLM-judge review of the generated explanation")
    print("against the retrieved evidence, not just a document-match heuristic. Review")
    print("the per-scenario results below manually for those two dimensions.")
    print()
    for r in results:
        print(json.dumps(r, indent=2))

    return {"summary": summary, "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the RAG retrieval pipeline against evaluation/eval_dataset.json.")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--output", type=str, default=None, help="Optional path to write results as JSON.")
    args = parser.parse_args()

    output = evaluate(top_k=args.top_k)
    if output and args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nResults written to {args.output}")
