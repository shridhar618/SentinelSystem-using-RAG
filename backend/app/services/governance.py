"""
SecureAI Governance Engine v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layer 1 — RBAC + NRL Response Filter      (role-based blocking/masking)
Layer 2 — AI Second-Layer Validator       (deep semantic safety scan)
Layer 3 — Risk Level Classifier           (Low / Medium / High)
Layer 4 — Explainability Engine           (human-readable block reasons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Constants & rule tables
# ─────────────────────────────────────────────────────────────────────────────

RISK_LOW_MAX    = 0.30
RISK_MEDIUM_MAX = 0.70
SUSPICIOUS_QUERY_THRESHOLD = 3

# Phase 9: default risk configuration. Every value here mirrors what was
# previously a hardcoded constant used directly in the scoring functions --
# this dict is now the single source of defaults, and _compute_risk_score/
# _classify_risk take an optional `config` override so an admin's saved
# RiskConfiguration values (see app/services/risk_config_service.py) can be
# threaded through without this module ever importing Flask/SQLAlchemy
# itself. Order of the weight_* keys matches LAYER2_RULE_GROUPS below.
DEFAULT_RISK_CONFIG = {
    "risk_threshold_low_max": RISK_LOW_MAX,
    "risk_threshold_medium_max": RISK_MEDIUM_MAX,
    "cumulative_risk_case_threshold": 1.50,
    "weight_cybersecurity_threat": 0.6,
    "weight_malware_attack_tooling": 0.8,
    "weight_data_exfiltration": 1.0,
    "weight_sensitive_pii": 0.7,
    "weight_insider_threat": 1.0,
}

# ── Layer 1: rule groups (Phase 8 generalization) ────────────────────────────
# Previously every rule below was only ever checked for role == "intern",
# meaning Manager/Supervisor/Software Engineer/Admin accounts received zero
# filtering -- including for credential and SSN requests. That contradicted
# Evolish's Information Security Policy (§4.3: credentials are never
# disclosed to any role) and Access Control Policy (§4.6: Manager is not
# granted view_employee_salary). This
# split makes the engine check the real Phase 1 permission model instead of
# a hardcoded role name, so every role is now held to the policy it actually
# describes rather than only interns being enforced.
#
# UNIVERSAL_BLOCKED_RULES: never allowed, for any role, any permission.
UNIVERSAL_BLOCKED_RULES = [
    (r"\bpassword\b",                "password information"),
    (r"\bcredential",                "credential data"),
    (r"\bapi[_\s]?key\b",           "API key material"),
    (r"\bssn\b",                     "Social Security Number"),
    (r"\bsocial\s*security\b",      "Social Security information"),
    (r"\bcredit\s*card\b",          "credit card data"),
    (r"\bbank\s*account\b",         "banking information"),
    (r"\bprivate\s*key\b",          "private key material"),
    # Data Classification and Handling Policy §4.9 / §4.10 (Evolish is an
    # Indian FinTech: Aadhaar, PAN, CVV and UPI PIN are never disclosed).
    (r"\baadh?aar\b",                "Aadhaar number"),
    (r"\bpan\s*(?:numbers?|cards?|details|no\b)", "PAN details"),
    (r"\b(?:cvv|cvc)\b",             "card security code"),
    (r"\bupi\s*pin\b",              "UPI PIN"),
]

# PERMISSION_GATED_RULES: blocked only for a role that lacks the named
# permission (so HR/Admin/Manager -- which hold these permissions -- are
# correctly let through, while Intern/Software Engineer/Supervisor -- which
# don't -- are blocked, matching Access Control Policy §4.13-§4.15).
PERMISSION_GATED_RULES = [
    (r"\bsalar(?:y|ies)\b",          "salary/compensation data",            "view_employee_salary"),
    (r"\bcompensation\b",            "compensation information",            "view_employee_salary"),
    (r"\bpay\s*scale\b",             "pay scale details",                   "view_employee_salary"),
    (r"\bpayroll\b",                 "payroll data",                        "view_employee_salary"),
    (r"\bpersonal\s*data\b",         "personal data records",               "view_employee_pii"),
    (r"\bpii\b",                     "personally identifiable information", "view_employee_pii"),
    (r"\b(?:phone|mobile|contact)\s*(?:numbers?|details|info\w*)\b", "employee contact details", "view_employee_pii"),
    (r"\bhome\s*address(?:es)?\b",   "home address",                        "view_employee_pii"),
    (r"\bdate\s*of\s*birth\b",       "date of birth",                       "view_employee_pii"),
    (r"\bemployee\s*(?:records?|directory|details|personal\s*info\w*)\b", "employee records", "view_employee_pii"),
    (r"\bpersonal\s*(?:details|information|info)\b", "personal details",   "view_employee_pii"),
    # Data Warehouse and Analytics Access Policy §4.2: raw transaction data
    # is for Data Engineers only; §4.3/§4.4: masked analytics tables are for
    # Data Engineers and Data Analysts, nobody else.
    (r"\b(?:raw|unmasked)\s+(?:transaction|payment|upi|loan|customer|warehouse)s?\s*(?:data|logs?|records?|tables?)\b",
     "raw warehouse data", "view_warehouse_raw_data"),
    (r"\b(?:masked|tokeni[sz]ed)\s+(?:\w+\s+)?(?:tables?|datasets?|data)\b|\bwarehouse\s+(?:tables?|datasets?|data)\b",
     "warehouse analytics data", "view_warehouse_masked_data"),
]

# INTERN_ONLY_CAUTION_RULES: kept as intern-specific for now (unchanged
# behavior) because there's no single Phase 1 permission that cleanly maps
# to "confidential/proprietary/classified" -- generalizing this bucket the
# same way as the two above would mean guessing at a permission boundary
# the org policies don't actually specify. Flagged as a known limitation
# rather than solved speculatively; see docs/PHASE_8_NOTES.md.
INTERN_ONLY_CAUTION_RULES = [
    (r"\bsecret\b",                  "secret/classified content"),
    (r"\bconfidential\b",            "confidential content"),
    (r"\bproprietary\b",             "proprietary information"),
    (r"\binternal\s*only\b",        "internal-only content"),
    (r"\bclassified\b",             "classified information"),
]

# Preserved for any external caller still importing the old name directly
# (e.g. a script or notebook) -- behaves exactly as before for intern-role
# detection, since it's the union of all three groups' labels.
INTERN_BLOCKED_RULES = (
    [(p, l) for p, l, _perm in PERMISSION_GATED_RULES]
    + UNIVERSAL_BLOCKED_RULES
    + INTERN_ONLY_CAUTION_RULES
)

# ── Layer 1: HR PII masking rules ────────────────────────────────────────────
HR_MASKED_RULES = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
     "[EMAIL REDACTED]", "email address"),
    (r"\b(\+?\d[\d\s\-().]{7,}\d)\b",
     "[PHONE REDACTED]", "phone number"),
    (r"\b\d{3}-\d{2}-\d{4}\b",
     "[SSN REDACTED]", "SSN-format number"),
    (r"\b(?:\d[ -]?){13,16}\b",
     "[CARD REDACTED]", "card number"),
    (r"(?:\$|₹|\b(?:INR|Rs\.?)\s?)[\d,]+(?:\.\d{2})?(?:\s*(?:k|K|thousand|million|billion|lakhs?|crores?))?\b",
     "[AMOUNT REDACTED]", "salary/financial figure"),
    (r"(?i)password\s*[:=]\s*\S+",
     "password: [REDACTED]", "inline password"),
]

# ── Layer 2: Deep semantic risk signal groups ─────────────────────────────────
LAYER2_RULE_GROUPS = [
    ("cybersecurity threat language", [
        "hack", "exploit", "bypass", "inject", "sql injection",
        "xss", "csrf", "rce", "privilege escalation", "zero-day",
        "reverse shell", "payload", "c2 server", "exfiltrat",
    ]),
    ("malware / attack tooling", [
        "malware", "ransomware", "trojan", "rootkit", "keylogger",
        "spyware", "botnet", "ddos", "phishing", "spear phish",
        "brute force", "credential dump", "mimikatz",
    ]),
    ("data exfiltration signals", [
        "dump database", "export all", "extract records",
        "full database", "all passwords", "all credentials",
        "user table", "shadow file", "/etc/passwd",
    ]),
    ("sensitive PII disclosure", [
        "social security", "date of birth", "home address",
        "passport number", "driver license", "medical record",
        "health information", "financial record",
    ]),
    ("insider threat indicators", [
        "cover tracks", "delete logs", "clear audit", "hide activity",
        "disable monitoring", "turn off logging", "evade detection",
    ]),
]

_ALL_RISK_KEYWORDS = [kw for _, group in LAYER2_RULE_GROUPS for kw in group]


# ─────────────────────────────────────────────────────────────────────────────
# Data transfer objects
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FilterResult:
    filtered_response: str
    status: str
    risk_score: float
    risk_level: str
    reason: Optional[str] = None
    triggered_rules: list = field(default_factory=list)
    is_high_risk_alert: bool = False
    validator_notes: list = field(default_factory=list)
    recommended_action: Optional[str] = None
    policy_evidence: list = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Policy evidence — static reference, NOT retrieval-augmented generation
# ─────────────────────────────────────────────────────────────────────────────
# This maps each rule label this engine can trigger to the specific
# organization policy document (and clause) that actually governs it --
# see backend/policy_corpus/organization/*.md (the eight Evolish Technologies
# policies, EV-SEC-001..008; "§4.2" is the "## 4.2 ..." heading of the named
# document). It is a deterministic lookup
# table, not a similarity search over embeddings: the RAG pipeline (Phase 6)
# will eventually retrieve evidence dynamically across the full policy
# corpus (including the NIST/OWASP/DPDP external frameworks), and should
# supersede this table rather than run alongside it as a second, conflicting
# source of citations. Every citation below points to a clause that was
# actually authored to describe this exact rule, so this is accurate today,
# not a placeholder -- but its coverage is limited to the 8 org documents on
# purpose, since verifying accuracy against a hand-written table is only
# tractable for a small, fully-authored corpus.

_ISP = "Information Security Policy"
_DCH = "Data Classification and Handling Policy"
_ACP = "Access Control Policy"
_DWA = "Data Warehouse and Analytics Access Policy"
_AUP = "Acceptable Use of AI Tools Policy"
_DPP = "Data Privacy Policy"
_HRP = "HR and Employee Records Policy"
_IRP = "Incident Response and Security Monitoring Policy"

_SALARY_CITATIONS = [f"{_HRP} §4.2", f"{_ACP} §4.14"]
_CREDENTIAL_CITATIONS = [f"{_ISP} §4.3", f"{_DCH} §4.5"]
_IDENTIFIER_CITATIONS = [f"{_DCH} §4.9"]
_PAYMENT_DATA_CITATIONS = [f"{_DCH} §4.10"]
_PERSONAL_DATA_CITATIONS = [f"{_DPP} §4.4", f"{_ACP} §4.15"]
_EMPLOYEE_RECORD_CITATIONS = [f"{_HRP} §4.3", f"{_ACP} §4.15"]

_INTERN_RULE_POLICY_MAP = {
    # Permission-gated: view_employee_salary
    "salary/compensation data": _SALARY_CITATIONS,
    "compensation information": _SALARY_CITATIONS,
    "pay scale details": _SALARY_CITATIONS,
    "payroll data": _SALARY_CITATIONS,
    # Universal: credentials and secrets
    "password information": _CREDENTIAL_CITATIONS,
    "credential data": _CREDENTIAL_CITATIONS,
    "API key material": _CREDENTIAL_CITATIONS,
    "private key material": _CREDENTIAL_CITATIONS,
    # Universal: government-issued identifiers
    "Social Security Number": _IDENTIFIER_CITATIONS,
    "Social Security information": _IDENTIFIER_CITATIONS,
    "Aadhaar number": _IDENTIFIER_CITATIONS,
    "PAN details": _IDENTIFIER_CITATIONS,
    # Universal: payment card and bank account data
    "credit card data": _PAYMENT_DATA_CITATIONS,
    "banking information": _PAYMENT_DATA_CITATIONS,
    "card security code": _PAYMENT_DATA_CITATIONS,
    "UPI PIN": _PAYMENT_DATA_CITATIONS,
    # Intern-only caution rules
    "secret/classified content": [f"{_ACP} §4.2", f"{_DCH} §4.5"],
    "classified information": [f"{_ACP} §4.2", f"{_DCH} §4.5"],
    "confidential content": [f"{_ACP} §4.2", f"{_DCH} §4.4"],
    "proprietary information": [f"{_ACP} §4.2", f"{_DCH} §4.4"],
    "internal-only content": [f"{_ACP} §4.2", f"{_DCH} §4.3"],
    # Permission-gated: view_employee_pii
    "personal data records": _PERSONAL_DATA_CITATIONS,
    "personally identifiable information": _PERSONAL_DATA_CITATIONS,
    "employee contact details": _EMPLOYEE_RECORD_CITATIONS,
    "home address": _EMPLOYEE_RECORD_CITATIONS,
    "date of birth": _EMPLOYEE_RECORD_CITATIONS,
    "employee records": _EMPLOYEE_RECORD_CITATIONS,
    "personal details": _EMPLOYEE_RECORD_CITATIONS,
    # Permission-gated: data warehouse
    "raw warehouse data": [f"{_DWA} §4.2", f"{_ACP} §4.13"],
    "warehouse analytics data": [f"{_DWA} §4.3", f"{_DWA} §4.4"],
}

# Contextual threat categories (services/threat_detection.py) -> governing clauses.
_THREAT_CATEGORY_POLICY_MAP = {
    "credential_theft": [f"{_ISP} §4.3", f"{_IRP} §4.5"],
    "private_conversation_access": [f"{_DPP} §4.5", f"{_ACP} §4.1"],
    "database_exploitation": [f"{_ISP} §4.6", f"{_DWA} §4.8"],
    "auth_bypass": [f"{_ACP} §4.17", f"{_ISP} §4.6"],
    "unauthorized_access": [f"{_ACP} §4.1", f"{_ISP} §4.6"],
    "sensitive_data_extraction": [f"{_DPP} §4.16", f"{_DWA} §4.8"],
    "privilege_escalation": [f"{_ACP} §4.16", f"{_IRP} §4.5"],
    "prompt_injection": [f"{_AUP} §4.5", f"{_IRP} §4.5"],
}

# Which permission makes a non-bulk "sensitive data" request legitimate for a role.
_AUTHORIZED_DATA_PATTERNS = [
    (re.compile(r"\b(?:salar(?:y|ies)|compensation|pay\s*scale|payroll|ctc|stipend)\b", re.I), "view_employee_salary"),
    (re.compile(r"\b(?:phone|mobile|contact|e-?mail|personal\s*(?:data|details|info\w*)|pii|employee\s*(?:records?|details|directory))\b", re.I), "view_employee_pii"),
]
# A question ABOUT a policy ("how are credentials handled under the privacy
# policy?") is not a request FOR the data. Keyword rules on the query are
# skipped for such questions unless they also contain an acquisition verb.
_POLICY_QUESTION_RE = re.compile(
    r"\b(?:polic(?:y|ies)|rules?|guidelines?|handled|handling|allowed|permitted|prohibited|procedures?|"
    r"classif\w*|who\s+can|compliance)\b", re.I)
_ACQUISITION_RE = re.compile(
    r"\b(?:give|show|send|share|reveal|leak|dump|export|fetch|provide|list|display|print|steal|retrieve)\b"
    r"|\btell\s+me\s+(?:the|his|her|their|\w+'s)\b|\bget\s+me\b|\b\w+'s\s+(?:password|salary|phone|address|credentials?|e-?mail)\b",
    re.I)


def is_policy_question(query: str) -> bool:
    return bool(_POLICY_QUESTION_RE.search(query or "")) and not _ACQUISITION_RE.search(query or "")


# Threat-intent score (0-100) at or above which a request is RESTRICTED.
# Below it but >= 30 (MEDIUM) the request is answered with a caution.
THREAT_BLOCK_SCORE = 40

_BULK_RE = re.compile(r"\b(?:all|every|everyone|full|complete|entire|bulk|export|dump|download|scrape|harvest|exfiltrat\w*)\b", re.I)

_LAYER2_CATEGORY_POLICY_MAP = {
    "cybersecurity threat language": [f"{_ISP} §4.6", f"{_IRP} §4.4"],
    "malware / attack tooling": [f"{_ISP} §4.7", f"{_IRP} §4.4"],
    "data exfiltration signals": [f"{_DWA} §4.8", f"{_DPP} §4.16"],
    "sensitive PII disclosure": [f"{_DPP} §4.4", f"{_IRP} §4.4"],
    "insider threat indicators": [f"{_ISP} §4.9", f"{_IRP} §4.11"],
}

_HR_MASK_POLICY_MAP = {
    "email address": [f"{_DCH} §4.12"],
    "phone number": [f"{_DCH} §4.12"],
    "SSN-format number": [f"{_DCH} §4.12", f"{_DCH} §4.9"],
    "card number": [f"{_DCH} §4.12", f"{_DCH} §4.10"],
    "salary/financial figure": [f"{_DCH} §4.12", f"{_HRP} §4.8"],
    "inline password": [f"{_DCH} §4.12", f"{_ISP} §4.3"],
}


def _policy_evidence_for(triggered_rules, validator_notes, hr_masked_labels=None) -> list:
    """Deterministic mapping only -- see module docstring above."""
    citations = []
    for label in triggered_rules or []:
        for citation in _INTERN_RULE_POLICY_MAP.get(label, []):
            if citation not in citations:
                citations.append(citation)
    for label in hr_masked_labels or []:
        for citation in _HR_MASK_POLICY_MAP.get(label, []):
            if citation not in citations:
                citations.append(citation)
    for note in validator_notes or []:
        for category, citation_list in _LAYER2_CATEGORY_POLICY_MAP.items():
            if category in note:
                for citation in citation_list:
                    if citation not in citations:
                        citations.append(citation)
    return citations


def _recommended_action_for(status: str, has_policy_evidence: bool = True) -> str:
    if status == "blocked":
        if not has_policy_evidence:
            # Phase 22 requirement, exact wording: a consequential decision
            # (blocking a request) must never be presented as confidently
            # policy-grounded when no specific citation actually backs it --
            # better to say so plainly and route to a human than imply
            # certainty the system doesn't have.
            return (
                "Insufficient policy evidence to make a reliable governance decision. "
                "This request has been blocked out of caution based on risk signals alone. "
                "An administrator should review this case."
            )
        return (
            "Do not attempt to access this information through the AI assistant. "
            "If you have a legitimate business need, contact HR or an authorized "
            "administrator for manual review."
        )
    if status == "filtered":
        return (
            "Review the masked response above. If you need the unredacted value "
            "for an authorized purpose, request it through the appropriate secure "
            "channel rather than the AI assistant."
        )
    return "No action required. Request was within policy for your role."


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def adjust_threat_for_role(threat, query: str, permissions: list):
    """Role-aware threat scoring. The threat detector is role-blind, so a
    targeted, non-bulk request for data the requester's role IS authorized
    to see (e.g. HR asking for one employee's salary) would otherwise score
    the same as an Intern asking for it. That case is dampened; bulk
    extraction stays high for everyone (Data Privacy Policy §4.16; HR and
    Employee Records Policy §4.7)."""
    if threat is None or not threat.categories:
        return threat
    if set(threat.categories) != {"sensitive_data_extraction"} or _BULK_RE.search(query or ""):
        return threat
    needed = [perm for rx, perm in _AUTHORIZED_DATA_PATTERNS if rx.search(query or "")]
    if not needed or not all(perm in (permissions or []) for perm in needed):
        return threat
    from dataclasses import replace
    from app.services.threat_detection import score_to_level

    score = int(round(threat.score * 0.3))
    return replace(
        threat,
        score=score,
        level=score_to_level(score),
        signals=[*threat.signals, "Requester's role is authorized for this data class (targeted, non-bulk request)"],
    )


def _apply_threat(result: FilterResult, threat, config) -> FilterResult:
    """Fold the contextual intent assessment into the decision: HIGH/CRITICAL
    intent is RESTRICTED (Incident Response and Security Monitoring Policy
    §4.5), MEDIUM raises risk and
    adds a caution, LOW only contributes its score."""
    if threat is None or threat.score <= 0:
        return result
    threat_risk = round(threat.score / 100, 3)
    labels = [f"threat: {_threat_label(c)}" for c in threat.categories]
    signal_note = f"Intent analysis: {threat.score}/100 ({threat.level})" + (
        f" - {'; '.join(threat.signals[:3])}" if threat.signals else ""
    )
    result.validator_notes = [*result.validator_notes, signal_note]
    for category in threat.categories:
        for citation in _THREAT_CATEGORY_POLICY_MAP.get(category, []):
            if citation not in result.policy_evidence:
                result.policy_evidence.append(citation)

    if threat.score >= THREAT_BLOCK_SCORE:
        result.risk_score = max(result.risk_score, threat_risk, 0.75)
        result.risk_level = "high"
        for label in labels:
            if label not in result.triggered_rules:
                result.triggered_rules.append(label)
        if result.status != "blocked":
            categories = ", ".join(_threat_label(c) for c in threat.categories) or "malicious intent"
            explanation = (
                f"This request is blocked because it shows high-risk intent ({threat.score}/100): {categories}. "
                "A single high-risk request is restricted by default and logged as a security event "
                "(Incident Response and Security Monitoring Policy §4.5)."
            )
            guidance = (
                "Requests aimed at attacking systems, bypassing controls, or obtaining other people's data or "
                "credentials are not permitted for any role. If this is legitimate security work, contact the "
                "Security team."
            )
            result.status = "blocked"
            result.filtered_response = (
                "Alert: Request blocked by SecureAI policy.\n"
                f"Why it was blocked: {explanation}\n"
                f"What to do: {guidance}"
            )
            result.reason = f"{explanation} {guidance}"
        return result

    if threat_risk > result.risk_score:
        result.risk_score = threat_risk
        result.risk_level = _classify_risk(threat_risk, config)
    if threat.level == "medium" and result.status != "blocked":
        for label in labels:
            if label not in result.triggered_rules:
                result.triggered_rules.append(label)
        result.reason = result.reason or (
            f"Caution: this request contains possible risk signals ({', '.join(_threat_label(c) for c in threat.categories) or 'attack vocabulary'}). "
            "It was answered, but it has been logged and counts toward your cumulative risk."
        )
        result.filtered_response = (
            "Caution: this request contains possible risk signals and has been logged for review.\n\n"
            + result.filtered_response
        )
    return result


def _threat_label(category: str) -> str:
    from app.services.threat_detection import CATEGORY_LABELS

    return CATEGORY_LABELS.get(category, category)


def apply_governance(response: str, query: str, role: str, permissions: Optional[list] = None, risk_config: Optional[dict] = None, threat=None, response_trusted: bool = False) -> FilterResult:
    """
    permissions: the requester's effective permission list (see
    app.services.permissions.permissions_for_role). If not supplied, this
    looks the role up itself so existing callers that haven't been updated
    keep working -- but callers should pass this explicitly where possible,
    since it's the actual source of truth (a role's permissions can be
    reconfigured without this module knowing about it otherwise).

    risk_config: admin-configurable weights/thresholds (Phase 9), shaped
    like DEFAULT_RISK_CONFIG. If not supplied, DEFAULT_RISK_CONFIG is used --
    this keeps the module runnable and testable with zero Flask/DB
    dependency, while a Flask-aware caller can load real, saved admin
    configuration via app.services.risk_config_service.load_risk_config().
    """
    if permissions is None:
        from app.services.permissions import permissions_for_role
        permissions = permissions_for_role(role)
    config = {**DEFAULT_RISK_CONFIG, **(risk_config or {})}

    # response_trusted: the response was composed by SecureAI itself from
    # vetted policy text / scoped sample data (offline mode), so keyword
    # rules evaluate the user's request only -- otherwise a policy excerpt
    # that merely *mentions* "passwords" would block an innocent question.
    scan_response = "" if response_trusted else response

    risk_score = _compute_risk_score(query, scan_response, config)
    risk_level = _classify_risk(risk_score, config)
    validator_notes = _layer2_validator(scan_response, query)

    if validator_notes and risk_level != "high":
        risk_score = min(risk_score + 0.25, 1.0)
        risk_level = _classify_risk(risk_score, config)

    policy_question = is_policy_question(query)
    result = _filter_by_permissions(query, scan_response, role, permissions, risk_score, risk_level,
                                    policy_question=policy_question)
    if policy_question and result.status == "allowed" and _detect_universal_blocks(query, "") + _detect_permission_gated_blocks(query, ""):
        validator_notes.append("Question is about policy on a restricted topic; answered with policy text only, no data disclosed.")
    if result.status == "allowed":
        result.filtered_response = response

    if role == "hr":
        # HR-specific field masking runs in addition to (not instead of)
        # the permission-based blocking above -- HR holds view_employee_pii
        # and view_employee_salary, so it won't be blocked by those rules,
        # but inline PII that slips into a response text still gets masked.
        # Fields the request actually asked for are not masked (Data
        # Classification and Handling Policy §4.12/§4.13: per-field relevance).
        hr_result = _filter_hr(result.filtered_response, result.risk_score, result.risk_level, query=query)
        if hr_result.status == "filtered" and result.status == "allowed":
            hr_result.policy_evidence = result.policy_evidence + hr_result.policy_evidence
            result = hr_result

    result.validator_notes = validator_notes
    result = _apply_threat(result, threat, config)
    result.is_high_risk_alert = (result.risk_level == "high")
    # Merge any policy evidence already set by the role filter (e.g. intern
    # blocklist citations) with evidence derived from Layer-2 validator hits,
    # which apply regardless of role.
    layer2_evidence = _policy_evidence_for([], validator_notes)
    for citation in layer2_evidence:
        if citation not in result.policy_evidence:
            result.policy_evidence.append(citation)
    result.recommended_action = _recommended_action_for(result.status, has_policy_evidence=bool(result.policy_evidence))
    return result


def compute_query_sensitivity(query: str) -> bool:
    q = query.lower()

    if any(kw in q for kw in _ALL_RISK_KEYWORDS):
        return True

    return any(re.search(pattern, q, re.IGNORECASE) for pattern, _ in INTERN_BLOCKED_RULES)


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 — Role/permission filters
# ─────────────────────────────────────────────────────────────────────────────

def _filter_by_permissions(query, response, role, permissions, risk_score, risk_level, policy_question=False):
    """Applies UNIVERSAL_BLOCKED_RULES (every role) and PERMISSION_GATED_RULES
    (only roles lacking the relevant permission) to any role -- this is what
    replaced the old "only intern gets filtered" behavior. Intern additionally
    gets INTERN_ONLY_CAUTION_RULES, preserving its prior (unchanged) behavior
    for that bucket.
    """
    scan_query = "" if policy_question else query
    triggered = _detect_universal_blocks(scan_query, response)
    triggered += [
        label for label in _detect_permission_gated_blocks(scan_query, response)
        if _permission_for_label(label) not in permissions
    ]
    if role == "intern":
        triggered += _detect_intern_caution_blocks(scan_query, response)

    if triggered:
        joined = ", ".join(triggered)
        explanation = (
            f"This request is blocked because it asks about restricted information: {joined}. "
            "Your role does not have permission to access confidential, credential, compensation, "
            "or regulated personal data of this kind."
        )
        guidance = (
            "Your current role's permissions do not cover that data. "
            "If you need legitimate access, contact HR or an admin, or ask for a high-level policy summary instead."
        )
        return FilterResult(
            filtered_response=(
                "Alert: Request blocked by SecureAI policy.\n"
                f"Why it was blocked: {explanation}\n"
                f"Why you cannot ask this: {guidance}"
            ),
            status="blocked",
            risk_score=max(risk_score, 0.75),
            risk_level="high",
            reason=f"{explanation} {guidance}",
            triggered_rules=triggered,
            is_high_risk_alert=True,
            policy_evidence=_policy_evidence_for(triggered, []),
        )
    return FilterResult(
        filtered_response=response,
        status="allowed",
        risk_score=risk_score,
        risk_level=risk_level,
    )


_HR_RELEVANT_FIELDS = [
    (re.compile(r"\b(?:salar(?:y|ies)|compensation|pay\s*scale|payroll|ctc|stipend)\b", re.I), {"salary/financial figure"}),
    (re.compile(r"\b(?:phone|mobile|contact)\b", re.I), {"phone number"}),
    (re.compile(r"\b(?:e-?mail|contact)\b", re.I), {"email address"}),
]


def _filter_hr(response, risk_score, risk_level, query=""):
    relevant = set()
    for rx, labels in _HR_RELEVANT_FIELDS:
        if rx.search(query or ""):
            relevant |= labels
    masked = response
    triggered = []
    for pattern, replacement, label in HR_MASKED_RULES:
        if label in relevant:
            continue
        new_masked, count = re.subn(pattern, replacement, masked, flags=re.IGNORECASE)
        if count > 0:
            triggered.append(label)
            masked = new_masked

    if triggered:
        joined = ", ".join(triggered)
        reason = (
            f"Response automatically redacted {len(triggered)} sensitive field(s): {joined}. "
            f"Data masked per HR data-handling policy."
        )
        return FilterResult(
            filtered_response=masked,
            status="filtered",
            risk_score=risk_score,
            risk_level=risk_level,
            reason=reason,
            triggered_rules=triggered,
            policy_evidence=_policy_evidence_for([], [], hr_masked_labels=triggered),
        )
    return FilterResult(
        filtered_response=response,
        status="allowed",
        risk_score=risk_score,
        risk_level=risk_level,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 — Validator
# ─────────────────────────────────────────────────────────────────────────────

def _layer2_validator(response, query):
    combined = (query + " " + response).lower()
    notes = []
    for category, keywords in LAYER2_RULE_GROUPS:
        hits = [kw for kw in keywords if kw in combined]
        if hits:
            sample = hits[:2]
            notes.append(
                f"Detected {category} signal "
                f"(matched: {', '.join(repr(h) for h in sample)})"
            )
    return notes


def _detect_intern_blocked_rules(query, response):
    """Kept for backward compatibility with any external caller still using
    the old name/behavior (union of all three rule groups)."""
    combined = f"{query or ''} {response or ''}"
    triggered = []
    for pattern, label in INTERN_BLOCKED_RULES:
        if re.search(pattern, combined, re.IGNORECASE) and label not in triggered:
            triggered.append(label)
    return triggered


def _permission_for_label(label: str) -> Optional[str]:
    for _pattern, rule_label, permission in PERMISSION_GATED_RULES:
        if rule_label == label:
            return permission
    return None


def _detect_universal_blocks(query, response):
    combined = f"{query or ''} {response or ''}"
    triggered = []
    for pattern, label in UNIVERSAL_BLOCKED_RULES:
        if re.search(pattern, combined, re.IGNORECASE) and label not in triggered:
            triggered.append(label)
    return triggered


def _detect_permission_gated_blocks(query, response):
    combined = f"{query or ''} {response or ''}"
    triggered = []
    for pattern, label, _permission in PERMISSION_GATED_RULES:
        if re.search(pattern, combined, re.IGNORECASE) and label not in triggered:
            triggered.append(label)
    return triggered


def _detect_intern_caution_blocks(query, response):
    combined = f"{query or ''} {response or ''}"
    triggered = []
    for pattern, label in INTERN_ONLY_CAUTION_RULES:
        if re.search(pattern, combined, re.IGNORECASE) and label not in triggered:
            triggered.append(label)
    return triggered


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 — Risk scoring + classification
# ─────────────────────────────────────────────────────────────────────────────

def _compute_risk_score(query, response, config=None):
    config = config or DEFAULT_RISK_CONFIG
    combined = (query + " " + response).lower()
    group_weights = [
        config["weight_cybersecurity_threat"],
        config["weight_malware_attack_tooling"],
        config["weight_data_exfiltration"],
        config["weight_sensitive_pii"],
        config["weight_insider_threat"],
    ]
    group_score = 0.0

    for (_, keywords), weight in zip(LAYER2_RULE_GROUPS, group_weights):
        hits = sum(1 for kw in keywords if kw in combined)
        if hits:
            group_score += min(hits / len(keywords), 1.0) * weight

    keyword_score = min(group_score / sum(group_weights), 1.0)
    length_score = min(len(response) / 6000, 0.25)

    intent_score = 0.0
    intent_phrases = [
        "how do i hack", "how to bypass", "give me all",
        "list all users", "show me passwords", "what are the credentials",
        "ignore previous", "disregard your instructions", "pretend you are",
    ]
    if any(p in combined for p in intent_phrases):
        intent_score = 0.3

    raw = keyword_score * 0.60 + length_score * 0.15 + intent_score * 0.25
    return round(min(raw, 1.0), 3)


def _classify_risk(score, config=None):
    config = config or DEFAULT_RISK_CONFIG
    if score <= config["risk_threshold_low_max"]:
        return "low"
    elif score <= config["risk_threshold_medium_max"]:
        return "medium"
    return "high"
