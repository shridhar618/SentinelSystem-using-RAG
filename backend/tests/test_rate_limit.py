"""
Phase 24 — login rate limiter tests. app.services.rate_limit has zero
Flask/DB dependency.
"""

import importlib

import pytest


@pytest.fixture(autouse=True)
def _fresh_state():
    """Reset the module's in-memory state between tests -- it's a module-
    level dict, so without this, tests would see each other's attempts."""
    from app.services import rate_limit
    rate_limit._attempts.clear()
    yield
    rate_limit._attempts.clear()


def test_allows_up_to_the_configured_limit():
    from app.services.rate_limit import is_rate_limited, record_attempt, MAX_ATTEMPTS

    ip, user = "10.0.0.1", "intern_bob"
    for _ in range(MAX_ATTEMPTS):
        assert not is_rate_limited(ip, user)
        record_attempt(ip, user)
    assert is_rate_limited(ip, user) is True


def test_different_ip_is_not_affected_by_another_ips_attempts():
    from app.services.rate_limit import is_rate_limited, record_attempt, MAX_ATTEMPTS

    user = "intern_bob"
    for _ in range(MAX_ATTEMPTS):
        record_attempt("10.0.0.1", user)
    assert is_rate_limited("10.0.0.1", user) is True
    assert is_rate_limited("10.0.0.99", user) is False


def test_reset_attempts_clears_the_counter():
    from app.services.rate_limit import is_rate_limited, record_attempt, reset_attempts, MAX_ATTEMPTS

    ip, user = "10.0.0.1", "intern_bob"
    for _ in range(MAX_ATTEMPTS):
        record_attempt(ip, user)
    assert is_rate_limited(ip, user) is True
    reset_attempts(ip, user)
    assert is_rate_limited(ip, user) is False


def test_username_matching_is_case_insensitive():
    """Prevents a trivial bypass where "Bob" and "bob" get separate counters."""
    from app.services.rate_limit import is_rate_limited, record_attempt, MAX_ATTEMPTS

    ip = "10.0.0.1"
    for _ in range(MAX_ATTEMPTS):
        record_attempt(ip, "Bob")
    assert is_rate_limited(ip, "bob") is True
