"""
Phase 24 — audit logging (Phase 12) and policy document retrieval
(Phase 6/14). Could not be executed in this sandbox -- see
docs/PHASE_24_NOTES.md.
"""

from app import db
from app.models.audit_log import AuditLog
from app.models.policy_document import PolicyDocument


def test_login_is_recorded_in_the_audit_trail(app, client):
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    with app.app_context():
        login_events = AuditLog.query.filter_by(event_type="login", username="admin").all()
        assert len(login_events) >= 1


def test_failed_login_is_recorded_as_login_failed(app, client):
    client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})
    with app.app_context():
        failed_events = AuditLog.query.filter_by(event_type="login_failed", username="admin").all()
        assert len(failed_events) >= 1
        assert failed_events[0].status == "blocked"


def test_chat_request_is_logged_with_full_governance_fields(app, client, auth_headers):
    client.post(
        "/api/chat",
        json={"message": "What is the salary of all data engineers?"},
        headers=auth_headers("intern_bob", "intern123"),
    )
    with app.app_context():
        log = AuditLog.query.filter_by(username="intern_bob").order_by(AuditLog.id.desc()).first()
        assert log is not None
        assert log.status == "blocked"
        assert log.risk_level == "high"
        assert log.recommended_action
        assert log.policy_evidence  # non-empty JSON list


def test_audit_logs_endpoint_filters_by_event_type(client, auth_headers):
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    res = client.get("/api/logs?event_type=login", headers=auth_headers("admin", "admin123"))
    assert res.status_code == 200
    body = res.get_json()
    assert all(log["event_type"] == "login" for log in body["logs"])


def test_pre_phase12_chat_rows_still_appear_under_ai_request_filter(app, client, auth_headers):
    """AuditLog rows written before Phase 12 have event_type=NULL and must
    still show up when filtering for "ai_request" -- this is the exact
    backward-compatibility behavior documented in Phase 12's notes."""
    with app.app_context():
        legacy_row = AuditLog(
            user_id=1, username="legacy_user", role="intern",
            query="old query", status="allowed", risk_score=0.1, risk_level="low",
            event_type=None,  # simulates a pre-Phase-12 row
        )
        db.session.add(legacy_row)
        db.session.commit()

    res = client.get("/api/logs?event_type=ai_request", headers=auth_headers("admin", "admin123"))
    assert res.status_code == 200
    usernames = [log["username"] for log in res.get_json()["logs"]]
    assert "legacy_user" in usernames


def test_policies_list_endpoint_returns_seeded_or_empty_corpus(client, auth_headers):
    """Doesn't assume ingestion has been run (it requires ML dependencies
    not installed in every environment) -- just confirms the endpoint
    itself works and returns the correct shape either way."""
    res = client.get("/api/policies", headers=auth_headers("admin", "admin123"))
    assert res.status_code == 200
    assert "documents" in res.get_json()


def test_disabling_a_policy_document_is_audited(app, client, auth_headers):
    with app.app_context():
        doc = PolicyDocument(name="Test Policy.md", category="Security", status="active")
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id

    res = client.put(
        f"/api/policies/{doc_id}/status",
        json={"status": "disabled"},
        headers=auth_headers("admin", "admin123"),
    )
    assert res.status_code == 200
    assert res.get_json()["document"]["status"] == "disabled"

    with app.app_context():
        change_events = AuditLog.query.filter_by(event_type="policy_change", resource="Test Policy.md").all()
        assert len(change_events) == 1
