"""
Phase 26 — Risk Engine Evaluation.

Unlike Phase 25's RAG evaluation, this one CAN run with zero extra
dependencies: app.services.governance has no Flask/SQLAlchemy requirement,
so this script needs nothing beyond the Python standard library plus
app.services.permissions/roles. Computes accuracy, precision, recall, F1,
and a confusion matrix comparing evaluation/eval_dataset.json's
expected_decision/expected_risk against the real engine's actual output.

Usage (from backend/):
    python scripts/evaluate_risk_engine.py
"""

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
DATASET_PATH = BACKEND_ROOT / "evaluation" / "eval_dataset.json"

STATUS_TO_DECISION = {"allowed": "ALLOWED", "filtered": "WARNING", "blocked": "RESTRICTED"}


def _confusion_matrix(labels, pairs):
    matrix = {expected: {predicted: 0 for predicted in labels} for expected in labels}
    for expected, actual in pairs:
        matrix[expected][actual] += 1
    return matrix


def _precision_recall_f1(labels, pairs):
    """Per-label and macro-averaged precision/recall/F1, computed directly
    from the (expected, actual) pairs -- no external ML library needed for
    a 3-class confusion matrix this small.
    """
    per_label = {}
    for label in labels:
        tp = sum(1 for e, a in pairs if e == label and a == label)
        fp = sum(1 for e, a in pairs if e != label and a == label)
        fn = sum(1 for e, a in pairs if e == label and a != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        per_label[label] = {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3), "support": tp + fn}

    macro_precision = sum(v["precision"] for v in per_label.values()) / len(labels)
    macro_recall = sum(v["recall"] for v in per_label.values()) / len(labels)
    macro_f1 = sum(v["f1"] for v in per_label.values()) / len(labels)
    return per_label, {"precision": round(macro_precision, 3), "recall": round(macro_recall, 3), "f1": round(macro_f1, 3)}


def evaluate():
    """
    IMPORTANT METHODOLOGICAL NOTE (discovered by actually running this
    script -- see docs/PHASE_26_NOTES.md): this harness evaluates each
    scenario with response="" -- i.e. it mirrors /compliance/check's
    "would this question be authorized" semantics, not the full /chat flow
    where an AI-generated response has already been produced. A decision
    that depends on RESPONSE content (HR's field-level PII masking, which
    scans the generated answer for inline PII, not the question) can never
    be correctly evaluated this way -- it will always score as the
    unmasked "ALLOWED" outcome, regardless of what the real AI response
    would have contained. This is not a risk-engine bug; it's an honest
    limitation of query-only evaluation. Scenario #9 in the dataset
    demonstrates exactly this and should be read as a methodology note,
    not a regression, when reviewing mismatches below.
    """
    from app.services.governance import apply_governance
    from app.services.permissions import permissions_for_role

    with open(DATASET_PATH) as f:
        dataset = json.load(f)["scenarios"]

    decision_pairs = []
    risk_pairs = []
    mismatches = []

    for scenario in dataset:
        result = apply_governance(
            response="",
            query=scenario["question"],
            role=scenario["user_role"],
            permissions=permissions_for_role(scenario["user_role"]),
        )
        actual_decision = STATUS_TO_DECISION.get(result.status, result.status.upper())
        actual_risk = result.risk_level.upper()

        decision_pairs.append((scenario["expected_decision"], actual_decision))
        risk_pairs.append((scenario["expected_risk"], actual_risk))

        if actual_decision != scenario["expected_decision"] or actual_risk != scenario["expected_risk"]:
            mismatches.append({
                "id": scenario["id"],
                "question": scenario["question"],
                "role": scenario["user_role"],
                "expected": {"decision": scenario["expected_decision"], "risk": scenario["expected_risk"]},
                "actual": {"decision": actual_decision, "risk": actual_risk},
                "notes": scenario.get("notes", ""),
            })

    decision_labels = ["ALLOWED", "WARNING", "RESTRICTED"]
    risk_labels = ["LOW", "MEDIUM", "HIGH"]

    decision_accuracy = sum(1 for e, a in decision_pairs if e == a) / len(decision_pairs)
    risk_accuracy = sum(1 for e, a in risk_pairs if e == a) / len(risk_pairs)

    decision_per_label, decision_macro = _precision_recall_f1(decision_labels, decision_pairs)
    risk_per_label, risk_macro = _precision_recall_f1(risk_labels, risk_pairs)

    report = {
        "total_scenarios": len(dataset),
        "decision_classification": {
            "accuracy": round(decision_accuracy, 3),
            "macro_avg": decision_macro,
            "per_label": decision_per_label,
            "confusion_matrix": _confusion_matrix(decision_labels, decision_pairs),
        },
        "risk_classification": {
            "accuracy": round(risk_accuracy, 3),
            "macro_avg": risk_macro,
            "per_label": risk_per_label,
            "confusion_matrix": _confusion_matrix(risk_labels, risk_pairs),
        },
        "mismatches": mismatches,
    }
    return report


if __name__ == "__main__":
    report = evaluate()
    print(json.dumps(report, indent=2))
