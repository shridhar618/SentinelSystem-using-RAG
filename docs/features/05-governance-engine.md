# 5. Governance Engine, Compliance Check & Risk Configuration

## Overview
The governance engine is the single place that decides whether an AI request/response is **allowed, filtered (masked) or blocked**, how risky it is, *why*, which policy clause applies, and what the user should do next. The chatbot (doc 4) and the standalone **Compliance Check** endpoint both call it. Its weights and thresholds are admin-editable through **Risk Configuration**.

## Who can use it
Engine: every governed request. Compliance check: any authenticated user. Risk configuration: roles with `manage_risk_configuration` (Admin).

## Tech stack
Pure Python (`re`, `dataclasses`), with no Flask/DB imports, so it is directly unit-testable. Configuration is loaded from the `risk_configuration` table via `services/risk_config_service.py`. Evaluation scripts live in `backend/scripts/evaluate_risk_engine.py` (dataset in `backend/evaluation/`).

## How it works: four layers
```
apply_governance(response, query, role, permissions, risk_config)
 Layer 1  RBAC + response filter
          • UNIVERSAL_BLOCKED_RULES  passwords, credentials, API keys, SSN, card,
                                     bank account, private keys → blocked for EVERY role
          • PERMISSION_GATED_RULES   salary/compensation → needs view_employee_salary
                                     personal data / PII → needs view_employee_pii
          • INTERN_ONLY_CAUTION      secret / confidential / proprietary / classified
          • HR masking               emails, phones, SSN-format, card numbers,
                                     currency amounts, inline passwords → [REDACTED]
 Layer 2  Semantic validator         5 keyword groups: cybersecurity threat,
                                     malware/attack tooling, data exfiltration,
                                     sensitive PII, insider threat
 Layer 3  Risk classifier            score = 0.60·keyword + 0.15·length + 0.25·intent
                                     low ≤ 0.30 < medium ≤ 0.70 < high
 Layer 4  Explainability             reason text, triggered rules, validator notes,
                                     policy evidence (rule → policy clause map),
                                     recommended action
→ FilterResult(status, filtered_response, risk_score, risk_level, reason, …)
```
- **Keyword score:** for each Layer-2 group, `min(hits / group_size, 1) × group weight`, normalised by the sum of weights.
- **Intent score:** 0.3 when phrases like "how to bypass", "show me passwords" or "ignore previous" appear.
- **Policy evidence** is a deterministic lookup from each triggered rule to the clause in `backend/policy_corpus/organization/*.md` (for example "Data Privacy & Classification Policy §5.1(b)").
- **Suspicious users:** `compute_query_sensitivity` increments `users.sensitive_query_count`; at 3 the user is flagged `is_suspicious`.

**Compliance Check** (`POST /api/compliance/check`) runs the same engine on a *hypothetical* query with an empty response, returning `decision / risk_level / risk_score / reason / violated_rules / recommendations / sources`. It is a "check before you ask" tool that needs no LLM call.

**Risk Configuration.** Seeded defaults (never overwritten on restart):

| Key | Default | Meaning |
|---|---|---|
| `risk_threshold_low_max` | 0.30 | Upper bound of LOW |
| `risk_threshold_medium_max` | 0.70 | Upper bound of MEDIUM |
| `cumulative_risk_case_threshold` | 1.50 | Cumulative risk that opens a governance case (doc 6) |
| `weight_*` (5 keys) | 0.6–1.0 | Layer-2 group weights |
| `ghost_threat_alert_threshold` | 50 | Threat score that raises a Ghost Mode alert (doc 12) |

Every change is audited with previous/new values.

## Key files
- `backend/app/services/governance.py`, `services/risk_config_service.py`
- `backend/app/routes/compliance.py`, `routes/risk_config.py`
- `backend/app/models/risk_configuration.py`

## API
| Method | Path | Access |
|---|---|---|
| POST | `/api/compliance/check` | JWT |
| GET | `/api/risk-config` | `manage_risk_configuration` |
| PUT | `/api/risk-config/<key>` | `manage_risk_configuration`: `{value, enabled}` |

## Limitations
- Keyword and regex based: deterministic and explainable, but paraphrases can evade it, and benign text mentioning a keyword may be flagged. See `docs/RISK_ENGINE.md` for evaluation results.
- The intern-only caution bucket is role-name based (no clean permission mapping exists in the policies).
