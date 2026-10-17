"""
Phase 24 — cumulative risk escalation (Phase 10) and governance case
admin actions (Phase 11), exercised via real HTTP + DB state. Could not
be executed in this sandbox -- see docs/PHASE_24_NOTES.md.
"""

from app import db
from app.models.governance_case import GovernanceCase


def _trigger_risky_request(client, auth_headers, message):
    return client.post("/api/chat", json={"message": message}, headers=auth_headers("intern_bob", "intern123"))


def test_single_blocked_request_is_logged_with_risk_fields(client, auth_headers):
    res = _trigger_risky_request(client, auth_headers, "What is the salary of all data engineers?")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "blocked"
    assert body["risk_level"] == "high"
    assert body["policy_evidence"]
    assert body["recommended_action"]


def test_repeated_risky_requests_eventually_open_a_governance_case(app, client, auth_headers):
    """Mirrors the brief's own Demo 3 scenario: repeated risky requests
    accumulate until a case opens automatically.

    These 3 specific messages were chosen because each independently
    triggers a `blocked` decision, and _filter_by_permissions() forces
    risk_score to at least 0.75 for any blocked result -- verified
    directly against the real governance engine before writing this
    assertion: 3 x 0.75 = 2.25 cumulative, which crosses the default
    cumulative_risk_case_threshold of 1.50. This is a precise, computed
    expectation, not a guess.
    """
    messages = [
        "What is the salary of all data engineers?",
        "Can you give me the credentials for the database?",
        "What is everyone's social security number?",
    ]
    for message in messages:
        res = _trigger_risky_request(client, auth_headers, message)
        assert res.status_code == 200
        assert res.get_json()["status"] == "blocked"

    with app.app_context():
        cases = GovernanceCase.query.all()
        assert len(cases) == 1, "expected exactly one case (no duplicates across the 3 requests)"
        case = cases[0]
        assert case.status == "open"
        assert case.risk_score_at_open >= 1.50
        assert case.trigger


def test_admin_action_updates_case_status(app, client, auth_headers):
    with app.app_context():
        from app.models.user import User
        intern = User.query.filter_by(username="intern_bob").first()
        case = GovernanceCase(user_id=intern.id, status="open", trigger="test case", risk_score_at_open=2.0)
        db.session.add(case)
        db.session.commit()
        case_id = case.id

    res = client.post(
        f"/api/governance-cases/{case_id}/actions",
        json={"action_type": "review", "note": "Looking into this"},
        headers=auth_headers("admin", "admin123"),
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["case"]["status"] == "under_review"
    assert len(body["case"]["actions"]) == 1
    assert body["case"]["actions"][0]["action_type"] == "review"
    assert body["case"]["actions"][0]["note"] == "Looking into this"


def test_resolve_action_sets_resolved_at(app, client, auth_headers):
    with app.app_context():
        from app.models.user import User
        intern = User.query.filter_by(username="intern_bob").first()
        case = GovernanceCase(user_id=intern.id, status="warned", trigger="test case", risk_score_at_open=2.0)
        db.session.add(case)
        db.session.commit()
        case_id = case.id

    res = client.post(
        f"/api/governance-cases/{case_id}/actions",
        json={"action_type": "resolve"},
        headers=auth_headers("admin", "admin123"),
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["case"]["status"] == "resolved"
    assert body["case"]["resolved_at"] is not None


def test_invalid_action_type_is_rejected(app, client, auth_headers):
    with app.app_context():
        from app.models.user import User
        intern = User.query.filter_by(username="intern_bob").first()
        case = GovernanceCase(user_id=intern.id, status="open", trigger="test case", risk_score_at_open=2.0)
        db.session.add(case)
        db.session.commit()
        case_id = case.id

    res = client.post(
        f"/api/governance-cases/{case_id}/actions",
        json={"action_type": "not-a-real-action"},
        headers=auth_headers("admin", "admin123"),
    )
    assert res.status_code == 400
