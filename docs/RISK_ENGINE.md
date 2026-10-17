# Risk Engine

SecureAI's risk engine is **transparent and rule-based. It is not machine learning.** Every score can be explained from the rules that fired. Source: `backend/app/services/governance.py` (pure Python, no Flask/DB dependency, which is why it is directly unit-testable).

> External frameworks (NIST AI RMF, OWASP GenAI, DPDP Act) are *knowledge sources* for the policy corpus. They do not define this score. The weights and thresholds below are this project's own implementation rules, informed by those sources.

## Principles
1. **RBAC decides authorization.** Permissions (`services/permissions.py`) decide whether a role may see a class of data.
2. **The rule engine decides the outcome.** The LLM never decides authorization. Retrieved policy text is never read by the decision logic.
3. **Humans decide consequences.** The system opens cases and alerts admins; only an admin action restricts, warns, or escalates.

## Pipeline for one request (`apply_governance`)
| Step | What happens |
|---|---|
| 1. Universal rules | Credentials, passwords, API keys, SSN, credit card, bank account, private key → **blocked for every role, including Admin** (Data Privacy Policy §5.1). |
| 2. Permission-gated rules | Salary/compensation → needs `view_employee_salary`; personal data/PII → needs `view_employee_pii`. Blocked only if the role lacks the permission. |
| 3. Intern caution rules | confidential / proprietary / classified / internal-only → blocked for Intern (no clean permission maps to this, so it stays role-specific). |
| 4. HR masking | HR may ask, but inline emails, phone numbers, SSN-format numbers, card numbers, salary figures and inline passwords in the *response* are masked → decision `WARNING`. |
| 5. Risk score | Layer-3 weighted score (below). Blocked requests are floored at 0.75 / HIGH. |
| 6. Layer-2 validator | Keyword groups add explainability signals; a hit adds +0.25 to the score (unless already HIGH). |
| 7. Evidence + action | Policy citations (static lookup, see below) and a recommended action. A **blocked decision with no citation** returns *"Insufficient policy evidence to make a reliable governance decision"* and routes to an administrator. |

Decision mapping used by the API: `allowed → ALLOWED`, `filtered → WARNING`, `blocked → RESTRICTED`.

## Score (0–1)
```
keyword_score = min( Σ over 5 groups[ min(hits/len(group), 1) × weight ] / Σ weights , 1 )
length_score  = min(len(response)/6000, 0.25)
intent_score  = 0.3 if an intent phrase matched ("how to bypass", "give me all", "ignore previous", ...)
score         = min( 0.60·keyword_score + 0.15·length_score + 0.25·intent_score , 1 )
```
| Layer-2 group | Default weight |
|---|---|
| cybersecurity threat language | 0.6 |
| malware / attack tooling | 0.8 |
| data exfiltration signals | 1.0 |
| sensitive PII disclosure | 0.7 |
| insider threat indicators | 1.0 |

**Bands:** LOW ≤ 0.30 · MEDIUM ≤ 0.70 · HIGH > 0.70.

## Configurable (Admin → Risk Configuration)
All weights and thresholds live in the `risk_configurations` table (seeded at startup, never overwritten on restart) and are edited via `PUT /api/risk-config/<key>` (permission `manage_risk_configuration`). Disabling a row falls back to the default instead of zeroing it. Every change is audit-logged with the previous and new value.

Keys: `risk_threshold_low_max`, `risk_threshold_medium_max`, `cumulative_risk_case_threshold`, `weight_cybersecurity_threat`, `weight_malware_attack_tooling`, `weight_data_exfiltration`, `weight_sensitive_pii`, `weight_insider_threat`.

## Cumulative risk and escalation (`services/risk_tracking.py`)
- Only MEDIUM/HIGH requests are tracked; LOW requests never accumulate.
- Each tracked request appends a `risk_events` row holding the running `cumulative_score` for that user.
- **Any single HIGH request** → immediate real-time alert to all admins.
- When cumulative ≥ `cumulative_risk_case_threshold` (default **1.50**) and the user has no unresolved case → a `governance_cases` row (`open`) and a separate alert. Only one unresolved case per user at a time.
- Admin actions: Review, Warn, Restrict, Restore, Escalate, Resolve, Note. **Restrict is enforced**: `/api/chat` returns 403 for a user with a `restricted` case until an admin Restores or Resolves it. Nothing is ever auto-terminated.

## Policy evidence
Citations such as `Role & Access Control Policy §3.2` come from a hand-verified lookup table that maps each rule label to the clause that governs it in the four organization policies (`backend/policy_corpus/organization/`). This is a deterministic table, **not** retrieval. The RAG pipeline (see `RAG_PIPELINE.md`) is a separate, optional component that is not wired into the live decision path.

## Evaluation (real, reproducible)
`python scripts/evaluate_risk_engine.py` runs 15 labelled scenarios (`evaluation/eval_dataset.json`). Recorded run (`evaluation/risk_engine_eval_results.json`): decision accuracy **80.0 %** (12/15), risk-level accuracy **86.7 %** (13/15), 3 mismatches.

## Known limitations (honest list)
- **Keyword coverage is narrow.** "personal addresses" does not match the PII regex (`personal data` / `pii`), so a Software Engineer asking for employee addresses is not blocked. A firewall-bypass question stays LOW because each group's hits are normalised by the group's keyword count, so a single hit moves the score very little.
- **Query-only evaluation can't see response-dependent masking** (HR masking scans the generated answer).
- WARNING-band support in the evaluation set is tiny (n=2); treat per-label numbers as indicative only.
- Intern-only "caution" rules are not generalized to other roles.
- The login rate limiter is in-memory and single-process.
