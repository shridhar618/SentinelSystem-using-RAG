"""
Phase 21 — minimal login rate limiting.

Deliberately dependency-free (no Flask-Limiter, no Redis) so it needs
nothing beyond what's already installed and works the moment the app
starts. This is intentionally scoped to what a single-process capstone
deployment needs, not a production-grade distributed rate limiter:

  - State is in-memory and resets on restart -- fine for one process,
    wrong for multiple worker processes/instances, which would each keep
    their own separate counts. A real production deployment should
    replace this with Flask-Limiter backed by Redis, or similar.
  - Keyed by (IP address, username) rather than username alone, so an
    attacker can't lock a real user out of their own account by
    deliberately failing their login from an unrelated IP -- this
    specifically rate-limits brute-force attempts, not the victim.
"""

import time
from collections import defaultdict

_attempts: dict[tuple, list] = defaultdict(list)

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


def is_rate_limited(ip: str, username: str) -> bool:
    key = (ip, username.lower())
    now = time.time()
    _attempts[key] = [t for t in _attempts[key] if now - t < WINDOW_SECONDS]
    return len(_attempts[key]) >= MAX_ATTEMPTS


def record_attempt(ip: str, username: str) -> None:
    key = (ip, username.lower())
    _attempts[key].append(time.time())


def reset_attempts(ip: str, username: str) -> None:
    """Called on a successful login so a legitimate user who mistypes their
    password a couple of times isn't left sitting near the limit."""
    _attempts.pop((ip, username.lower()), None)
