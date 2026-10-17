"""
Phase 24 — authentication and RBAC enforcement, exercised via real HTTP
requests against the Flask test client. Unlike test_governance_scenarios.py
and test_permissions_rbac.py, these genuinely need Flask/SQLAlchemy to run
and could NOT be executed in the sandbox this was authored in (no network
to pip install flask-sqlalchemy/flask-jwt-extended/etc.) -- see
docs/PHASE_24_NOTES.md for exactly what was and wasn't verified.

Seeded accounts used here (see app/__init__.py _seed_demo_users):
  admin / admin123, hr_jane / hr123, intern_bob / intern123
"""

from werkzeug.security import generate_password_hash

from app import db
from app.models.user import User


def test_login_succeeds_with_correct_password(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    body = res.get_json()
    assert "token" in body
    assert body["user"]["username"] == "admin"
    assert "permissions" in body


def test_login_fails_with_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})
    assert res.status_code == 401
    assert "error" in res.get_json()


def test_login_rate_limited_after_repeated_failures(client):
    """Phase 21's rate limiter -- 5 failed attempts allowed, the 6th blocked."""
    for _ in range(5):
        res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert res.status_code == 401
    res = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 429


def test_me_endpoint_requires_a_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code in (401, 422)  # flask-jwt-extended returns 422 for a missing/malformed header


def test_me_endpoint_returns_permissions(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers("intern_bob", "intern123"))
    assert res.status_code == 200
    body = res.get_json()
    assert "use_ai_assistant" in body["permissions"]
    assert "view_employee_salary" not in body["permissions"]


def test_chat_blocked_for_a_role_without_use_ai_assistant(app, client, auth_headers):
    """Phase 2's permission enforcement on /chat -- create a Guest user
    (no seeded Guest account exists) and confirm they're denied."""
    with app.app_context():
        db.session.add(User(
            username="guest_test",
            email="guest@test.com",
            password_hash=generate_password_hash("guest123"),
            role="guest",
        ))
        db.session.commit()

    res = client.post(
        "/api/chat",
        json={"message": "hello"},
        headers=auth_headers("guest_test", "guest123"),
    )
    assert res.status_code == 403
    assert res.get_json()["required_permission"] == "use_ai_assistant"


def test_governance_cases_endpoint_requires_admin_permission(client, auth_headers):
    res = client.get("/api/governance-cases", headers=auth_headers("intern_bob", "intern123"))
    assert res.status_code == 403


def test_governance_cases_endpoint_allows_admin(client, auth_headers):
    res = client.get("/api/governance-cases", headers=auth_headers("admin", "admin123"))
    assert res.status_code == 200
    assert "cases" in res.get_json()


def test_risk_config_endpoint_requires_manage_risk_configuration_permission(client, auth_headers):
    res = client.get("/api/risk-config", headers=auth_headers("intern_bob", "intern123"))
    assert res.status_code == 403
    res_admin = client.get("/api/risk-config", headers=auth_headers("admin", "admin123"))
    assert res_admin.status_code == 200
