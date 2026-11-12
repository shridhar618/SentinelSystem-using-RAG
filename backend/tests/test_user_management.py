"""Admin user management (routes/user_management.py): login history and
user CRUD, including the guard rails that stop an admin locking everyone out."""

from werkzeug.security import generate_password_hash

from app import db
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.message import Message
from app.models.user import User


def _admin(auth_headers):
    return auth_headers("admin", "admin123")


def _make_user(app, username="temp_user", role="intern"):
    with app.app_context():
        user = User(username=username, email=f"{username}@secureai.local",
                    password_hash=generate_password_hash("pw12345"), role=role)
        db.session.add(user)
        db.session.commit()
        return user.id


def test_non_admin_is_forbidden(client, auth_headers):
    headers = auth_headers("intern_bob", "intern123")
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    assert client.get("/api/admin/login-activity", headers=headers).status_code == 403
    assert client.get("/api/admin/users/summary", headers=headers).status_code == 403


def test_list_users_includes_login_stats_and_hides_secrets(client, auth_headers):
    client.post("/api/auth/login", json={"username": "hr_jane", "password": "wrong"})
    client.post("/api/auth/login", json={"username": "hr_jane", "password": "hr123"})
    res = client.get("/api/admin/users", headers=_admin(auth_headers))
    assert res.status_code == 200
    users = {u["username"]: u for u in res.get_json()["users"]}
    jane = users["hr_jane"]
    assert jane["login_count"] >= 1
    assert jane["failed_login_count"] >= 1
    assert jane["last_login"]
    assert "login_code" not in jane and "password_hash" not in jane


def test_list_users_filters(client, auth_headers):
    headers = _admin(auth_headers)
    res = client.get("/api/admin/users?q=jane", headers=headers)
    assert [u["username"] for u in res.get_json()["users"]] == ["hr_jane"]
    res = client.get("/api/admin/users?role=admin", headers=headers)
    assert all(u["role"] == "admin" for u in res.get_json()["users"])


def test_login_activity_records_ip_and_method(client, auth_headers):
    client.post("/api/auth/login", json={"username": "intern_bob", "password": "intern123"},
                headers={"User-Agent": "pytest-browser"})
    res = client.get("/api/admin/login-activity?username=intern_bob&event_type=login",
                     headers=_admin(auth_headers))
    assert res.status_code == 200
    event = res.get_json()["events"][0]
    assert event["event_type"] == "login"
    assert event["method"] == "password"
    assert event["ip"]
    assert event["user_agent"] == "pytest-browser"


def test_summary_counts(client, auth_headers):
    res = client.get("/api/admin/users/summary", headers=_admin(auth_headers))
    body = res.get_json()
    assert body["total_users"] == body["active_users"] + body["inactive_users"]
    assert body["logins_24h"] >= 1


def test_get_user_detail(app, client, auth_headers):
    uid = _make_user(app)
    res = client.get(f"/api/admin/users/{uid}", headers=_admin(auth_headers))
    assert res.status_code == 200
    body = res.get_json()
    assert body["user"]["username"] == "temp_user"
    assert body["delete_blockers"] == {}
    assert client.get("/api/admin/users/999999", headers=_admin(auth_headers)).status_code == 404


def test_update_user_fields_and_audit(app, client, auth_headers):
    uid = _make_user(app)
    res = client.put(f"/api/admin/users/{uid}", headers=_admin(auth_headers),
                     json={"username": "renamed", "email": "Renamed@Example.com", "role": "hr"})
    assert res.status_code == 200, res.get_json()
    user = res.get_json()["user"]
    assert (user["username"], user["email"], user["role"]) == ("renamed", "renamed@example.com", "hr")
    with app.app_context():
        log = AuditLog.query.filter_by(event_type="role_change").order_by(AuditLog.id.desc()).first()
        assert log and f"user:{uid}" == log.resource


def test_update_rejects_duplicates_and_bad_role(app, client, auth_headers):
    uid = _make_user(app)
    headers = _admin(auth_headers)
    assert client.put(f"/api/admin/users/{uid}", headers=headers, json={"username": "hr_jane"}).status_code == 409
    assert client.put(f"/api/admin/users/{uid}", headers=headers, json={"role": "wizard"}).status_code == 400
    assert client.put(f"/api/admin/users/{uid}", headers=headers, json={"email": "nope"}).status_code == 400


def test_deactivated_user_cannot_log_in_and_can_be_reactivated(app, client, auth_headers):
    uid = _make_user(app)
    headers = _admin(auth_headers)
    assert client.put(f"/api/admin/users/{uid}", headers=headers, json={"is_active": False}).status_code == 200
    assert client.post("/api/auth/login", json={"username": "temp_user", "password": "pw12345"}).status_code == 403
    assert client.put(f"/api/admin/users/{uid}", headers=headers, json={"is_active": True}).status_code == 200
    assert client.post("/api/auth/login", json={"username": "temp_user", "password": "pw12345"}).status_code == 200


def test_admin_cannot_lock_themselves_out(app, client, auth_headers):
    headers = _admin(auth_headers)
    with app.app_context():
        admin_id = User.query.filter_by(username="admin").first().id
    assert client.put(f"/api/admin/users/{admin_id}", headers=headers, json={"is_active": False}).status_code == 400
    assert client.put(f"/api/admin/users/{admin_id}", headers=headers, json={"role": "intern"}).status_code == 400
    assert client.delete(f"/api/admin/users/{admin_id}", headers=headers).status_code == 400


def test_one_admin_can_manage_another_admin(app, client, auth_headers):
    _make_user(app, "admin_two", role="admin")
    headers = auth_headers("admin_two", "pw12345")
    with app.app_context():
        admin_id = User.query.filter_by(username="admin").first().id
    assert client.put(f"/api/admin/users/{admin_id}", headers=headers, json={"is_active": False}).status_code == 200
    assert client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).status_code == 403


def test_reset_login_code(app, client, auth_headers):
    uid = _make_user(app)
    res = client.post(f"/api/admin/users/{uid}/reset-code", headers=_admin(auth_headers))
    assert res.status_code == 200
    code = res.get_json()["login_code"]
    assert client.post("/api/auth/login", json={"username": "temp_user", "password": "pw12345"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "temp_user", "login_code": code}).status_code == 200


def test_delete_user_removes_personal_data_but_keeps_audit(app, client, auth_headers):
    uid = _make_user(app)
    client.post("/api/auth/login", json={"username": "temp_user", "password": "pw12345"})
    with app.app_context():
        db.session.add(AttendanceRecord(user_id=uid, event_type="check_in", confidence=0.9, source="test"))
        db.session.commit()
    res = client.delete(f"/api/admin/users/{uid}", headers=_admin(auth_headers))
    assert res.status_code == 200, res.get_json()
    with app.app_context():
        assert db.session.get(User, uid) is None
        assert AttendanceRecord.query.filter_by(user_id=uid).count() == 0
        assert AuditLog.query.filter_by(user_id=uid, event_type="login").count() == 1
        assert AuditLog.query.filter_by(resource=f"user:{uid}", event_type="admin_action").count() == 1


def test_delete_blocked_when_user_has_linked_records(app, client, auth_headers):
    uid = _make_user(app)
    with app.app_context():
        jane = User.query.filter_by(username="hr_jane").first()
        db.session.add(Message(sender_id=uid, receiver_id=jane.id, content="hi"))
        db.session.commit()
    res = client.delete(f"/api/admin/users/{uid}", headers=_admin(auth_headers))
    assert res.status_code == 409
    assert res.get_json()["blockers"] == {"messages": 1}
    with app.app_context():
        assert db.session.get(User, uid) is not None
