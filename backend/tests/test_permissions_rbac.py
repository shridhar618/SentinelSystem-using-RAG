"""
Phase 24 — RBAC and permission model tests. Like test_governance_scenarios.py,
app.services.permissions/roles have zero Flask dependency and every test
here was actually executed during development.
"""

from app.services.permissions import (
    PERMISSION_CATALOG,
    ROLE_PERMISSION_MAP,
    DEFAULT_PERMISSIONS,
    permissions_for_role,
    role_has_permission,
)
from app.services.roles import GOVERNANCE_DEMO_ROLES, ROLE_CATALOG, normalize_role_name


def test_every_governance_demo_role_is_in_the_catalog():
    for role in GOVERNANCE_DEMO_ROLES:
        assert role in ROLE_CATALOG


def test_role_permission_map_keys_match_normalization():
    """Guards against a typo like "software Engineer" silently never
    matching normalize_role_name("software engineer") -> "Software Engineer"."""
    for role_name in ROLE_PERMISSION_MAP:
        assert normalize_role_name(role_name) == role_name


def test_every_granted_permission_exists_in_the_catalog():
    catalog_names = {name for name, _category, _description in PERMISSION_CATALOG}
    for role_name, perms in ROLE_PERMISSION_MAP.items():
        for permission in perms:
            assert permission in catalog_names, f"{role_name} grants unknown permission {permission!r}"


def test_intern_has_chat_but_not_salary_or_pii():
    assert role_has_permission("Intern", "use_ai_assistant") is True
    assert role_has_permission("Intern", "view_employee_salary") is False
    assert role_has_permission("Intern", "view_employee_pii") is False


def test_guest_has_no_chat_access():
    assert role_has_permission("Guest", "use_ai_assistant") is False


def test_hr_has_salary_and_pii_access():
    assert role_has_permission("HR", "view_employee_salary") is True
    assert role_has_permission("HR", "view_employee_pii") is True


def test_manager_has_pii_but_not_salary():
    """Role & Access Control Policy §3.5 -- Manager gets PII (for direct
    reports) but compensation review stays an HR function."""
    assert role_has_permission("Manager", "view_employee_pii") is True
    assert role_has_permission("Manager", "view_employee_salary") is False


def test_admin_has_every_permission():
    all_permissions = {name for name, _category, _description in PERMISSION_CATALOG}
    admin_permissions = set(permissions_for_role("Admin"))
    assert admin_permissions == all_permissions


def test_unmapped_legacy_role_gets_conservative_defaults():
    """A role not explicitly in ROLE_PERMISSION_MAP (e.g. "Developer",
    one of the ~24 legacy catalog roles) must default to the conservative
    DEFAULT_PERMISSIONS set, not be silently treated as fully trusted."""
    assert permissions_for_role("Developer") == DEFAULT_PERMISSIONS
    assert permissions_for_role("Finance") == DEFAULT_PERMISSIONS
    assert "manage_users" not in permissions_for_role("Developer")


def test_role_name_normalization_edge_cases():
    assert normalize_role_name("hr") == "HR"
    assert normalize_role_name("software engineer") == "Software Engineer"
    assert normalize_role_name("ui/ux designer") == "UI/UX Designer"
    assert normalize_role_name("guest") == "Guest"
