"""GET /api/users must not leak colleagues' monitoring state or emails."""

SENSITIVE = {"email", "is_suspicious", "sensitive_query_count", "flagged_at", "face_enrolled", "created_at"}


def test_non_admin_gets_only_public_fields(client, auth_headers):
    users = client.get("/api/users", headers=auth_headers("intern_bob", "intern123")).get_json()["users"]
    assert users, "expected at least one other user"
    for user in users:
        assert set(user) == {"id", "username", "role", "role_id", "is_active"}
        assert not SENSITIVE & set(user)


def test_admin_keeps_full_records(client, auth_headers):
    users = client.get("/api/users", headers=auth_headers("admin", "admin123")).get_json()["users"]
    assert users
    assert {"email", "is_suspicious", "sensitive_query_count"} <= set(users[0])


def test_caller_is_excluded(client, auth_headers, users):
    listed = client.get("/api/users", headers=auth_headers("hr_jane", "hr123")).get_json()["users"]
    assert users["hr_jane"] not in {u["id"] for u in listed}
