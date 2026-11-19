from app import db
from app.models.audit_log import AuditLog
from app.models.question_feedback import QuestionFeedback
from app.services import ledger


def _add_log(query="q", username="de_arjun"):
    entry = AuditLog(user_id=1, username=username, role="data_engineer", query_text=query, status="allowed")
    db.session.add(entry)
    db.session.commit()
    return entry.id


def test_admin_can_delete_a_log_and_chain_still_verifies(app, client, auth_headers):
    headers = auth_headers("admin", "admin123")
    with app.app_context():
        _add_log("before")
        target = _add_log("rude word")
        _add_log("after")
        db.session.add(QuestionFeedback(audit_log_id=target, user_id=1, value="unhelpful"))
        db.session.commit()

    res = client.delete(f"/api/logs/{target}", headers=headers)
    assert res.status_code == 200, res.get_json()

    with app.app_context():
        assert db.session.get(AuditLog, target) is None
        assert AuditLog.query.filter(AuditLog.query_text == "rude word").count() == 0
        assert QuestionFeedback.query.filter_by(audit_log_id=target).count() == 0
        assert AuditLog.query.filter_by(event_type="admin_action", resource=f"audit_log:{target}").count() == 1
        assert ledger.verify_chain(db.session)["ok"] is True

    listed = client.get("/api/logs", headers=headers, query_string={"per_page": 100}).get_json()["logs"]
    assert all(log["id"] != target for log in listed)


def test_non_admin_cannot_delete_logs(app, client, auth_headers):
    with app.app_context():
        target = _add_log()
    res = client.delete(f"/api/logs/{target}", headers=auth_headers("intern_bob", "intern123"))
    assert res.status_code == 403
    assert client.delete("/api/logs/999999", headers=auth_headers("admin", "admin123")).status_code == 404
