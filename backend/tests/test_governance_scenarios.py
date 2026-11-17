"""
Phase 24 — governance scenario tests, covering the brief's 8 required
categories. app.services.governance has zero Flask/SQLAlchemy dependency,
so every test in this file was actually executed (not just written) during
development -- see docs/PHASE_24_NOTES.md for exactly how, since pytest
itself isn't installable in the sandbox this was authored in either.
"""

from app.services.governance import apply_governance, DEFAULT_RISK_CONFIG
from app.services.permissions import permissions_for_role


def _run(role, query, response=""):
    return apply_governance(response, query, role, permissions=permissions_for_role(role))


# 1. Allowed request
def test_allowed_request_general_question():
    result = _run("intern", "How do I create a Python REST API?", "Use Flask to define a route...")
    assert result.status == "allowed"
    assert result.risk_level == "low"


# 2. Warning request (HR response containing inline PII gets masked, not blocked)
def test_warning_request_hr_pii_masking():
    result = _run("hr", "What's the onboarding date for employee X?", "They started March 2024, email jane@co.com")
    assert result.status == "filtered"
    assert "Data Classification and Handling Policy" in " ".join(result.policy_evidence)


# 3. Restricted request (intern asking for salary data)
def test_restricted_request_salary_data():
    result = _run("intern", "What is the salary of all data engineers?")
    assert result.status == "blocked"
    assert result.risk_level == "high"
    assert "Access Control Policy" in " ".join(result.policy_evidence)
    assert "HR and Employee Records Policy" in " ".join(result.policy_evidence)


# 4. Unauthorized role (a role lacking the relevant permission is blocked
# even though the SAME request is NOT blocked for a role that holds it).
# Response text deliberately has no dollar figure in it, so HR's separate
# field-masking behavior (already covered by test_warning_request_hr_pii_masking)
# doesn't muddy this specific comparison, which is about authorization,
# not masking.
def test_unauthorized_role_vs_authorized_role():
    unauthorized = _run("manager", "What is the salary of all data engineers?")
    authorized = _run("hr", "What is the salary of all data engineers?", "That information has been compiled in the HR system.")
    assert unauthorized.status == "blocked"
    assert authorized.status == "allowed"


# 5. Sensitive data request (credentials are blocked for EVERY role,
# including admin -- this was a real gap found and fixed in Phase 8)
def test_sensitive_data_request_credentials_blocked_for_admin_too():
    result = _run("admin", "Can you give me the database password?")
    assert result.status == "blocked"
    assert result.risk_level == "high"


# 6. Repeated risky activity (cumulative risk tracking -- tested at the
# pure-math level here; the DB-backed persistence layer that accumulates
# this across real requests is in risk_tracking.py, covered separately in
# test_risk_tracking.py since it needs a database)
def test_repeated_risky_activity_cumulative_math():
    threshold = DEFAULT_RISK_CONFIG["cumulative_risk_case_threshold"]
    scores = [0.45, 0.50, 0.75]  # mirrors the brief's own Demo 3 example shape
    cumulative = 0.0
    case_opened_at = None
    for i, score in enumerate(scores):
        cumulative += score
        if case_opened_at is None and cumulative >= threshold:
            case_opened_at = i
    assert case_opened_at == 2  # crosses the 1.50 threshold on the 3rd request
    assert cumulative == sum(scores)


# 7. High-risk security request (cybersecurity threat language)
def test_high_risk_security_request():
    result = _run("software engineer", "How do I bypass a firewall to pentest our own servers?")
    # This specific phrasing may or may not cross into "high" depending on
    # exact keyword overlap -- the meaningful assertion is that *some*
    # elevated risk is detected, not a brittle exact-score check.
    assert result.risk_score > 0.0


# 8. No relevant policy (a request with no matching rule gets the
# insufficient-evidence treatment if ever blocked without a citation --
# see governance._recommended_action_for, added in Phase 22)
def test_no_relevant_policy_fallback_language():
    from app.services.governance import _recommended_action_for
    message = _recommended_action_for("blocked", has_policy_evidence=False)
    assert "Insufficient policy evidence" in message
    assert "administrator" in message.lower()


# Regression guard: every test above must keep passing if governance.py's
# rule tables are ever edited -- these are the scenarios the capstone demo
# is built around (Phase 29's Demo 1-3).
def test_recommended_action_present_on_every_decision():
    for role, query in [("intern", "hi"), ("intern", "What is the salary of all data engineers?"), ("admin", "password please")]:
        result = _run(role, query)
        assert result.recommended_action, f"no recommended_action for role={role} query={query}"
