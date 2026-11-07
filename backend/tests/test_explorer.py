from sqlalchemy import text

from app import db
from app.models.audit_log import AuditLog
from app.services import ledger


def _admin(auth_headers):
    return auth_headers("admin", "admin123")


def _add_log(username="admin", status="allowed", **kw):
    entry = AuditLog(user_id=1, username=username, role="admin", query_text="q", status=status, **kw)
    db.session.add(entry)
    db.session.commit()
    return entry


def test_new_audit_rows_are_sealed_and_linked(app):
    with app.app_context():
        a = _add_log()
        b = _add_log()
        assert a.chain_hash and b.chain_hash
        assert b.chain_seq == a.chain_seq + 1
        assert b.chain_prev_hash == a.chain_hash
        assert ledger.verify_chain(db.session)["ok"] is True


def test_rows_inserted_without_the_orm_are_backfilled(app, client, auth_headers):
    with app.app_context():
        db.session.execute(text(
            "INSERT INTO audit_logs (user_id, username, role, query, status, timestamp) "
            "VALUES (1, 'legacy', 'admin', 'old', 'allowed', '2025-01-01 00:00:00')"
        ))
        db.session.commit()
    res = client.get("/api/explorer/verify", headers=_admin(auth_headers))
    body = res.get_json()
    assert res.status_code == 200
    assert body["ok"] is True and body["unsealed"] == 0
    with app.app_context():
        assert AuditLog.query.filter_by(username="legacy").one().chain_hash


def test_editing_a_sealed_row_is_detected(app, client, auth_headers):
    headers = _admin(auth_headers)
    with app.app_context():
        target = _add_log(username="victim")
        _add_log()
        seq = target.chain_seq
        db.session.execute(text("UPDATE audit_logs SET status = 'allowed', query = 'edited' WHERE id = :id"), {"id": target.id})
        db.session.commit()

    body = client.get("/api/explorer/verify", headers=headers).get_json()
    assert body["ok"] is False
    assert body["first_break"]["seq"] == seq
    assert body["first_break"]["kind"] == "content_mismatch"

    block = client.get(f"/api/explorer/blocks/{seq}", headers=headers).get_json()
    assert block["integrity"]["hash_valid"] is False


def test_deleting_a_row_is_detected(app, client, auth_headers):
    headers = _admin(auth_headers)
    with app.app_context():
        _add_log()
        middle = _add_log()
        _add_log()
        db.session.execute(text("DELETE FROM audit_logs WHERE id = :id"), {"id": middle.id})
        db.session.commit()
    kinds = {i["kind"] for i in client.get("/api/explorer/verify", headers=headers).get_json()["issues"]}
    assert {"sequence_gap", "broken_link"} <= kinds


def test_blocks_search_and_stats(app, client, auth_headers):
    headers = _admin(auth_headers)
    with app.app_context():
        entry = _add_log(username="searchable_user", status="blocked", risk_level="high")
        prefix = entry.chain_hash[:10]

    stats = client.get("/api/explorer/stats", headers=headers).get_json()
    assert stats["height"] >= 1 and stats["unsealed"] == 0
    assert stats["head"]["hash"]

    by_hash = client.get(f"/api/explorer/blocks?q={prefix}", headers=headers).get_json()
    assert any(b["hash"].startswith(prefix) for b in by_hash["blocks"])

    by_user = client.get("/api/explorer/blocks?q=searchable&status=blocked", headers=headers).get_json()
    assert by_user["total"] == 1 and by_user["blocks"][0]["risk_level"] == "high"


def test_explorer_is_admin_only(client, auth_headers):
    headers = auth_headers("intern_amy", "intern456")
    for path in ("stats", "blocks", "verify", "blocks/1"):
        assert client.get(f"/api/explorer/{path}", headers=headers).status_code == 403
