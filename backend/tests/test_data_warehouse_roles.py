"""Data Engineer / Data Analyst roles and the Evolish policy citations.

Covers the two warehouse permissions (Data Warehouse and Analytics Access
Policy §4.2-§4.4, Access Control Policy §4.8/§4.9) and checks that every
citation the governance engine can emit points at a real "## N.M" heading
in the named policy document, so the rule-to-citation table cannot drift
from the policy text.
"""

import re
from pathlib import Path

import pytest

from app.services import governance
from app.services.governance import apply_governance
from app.services.permissions import (
    PERMISSION_CATALOG,
    ROLE_PERMISSION_MAP,
    permissions_for_role,
    role_has_permission,
)
from app.services.roles import GOVERNANCE_DEMO_ROLES, ROLE_CATALOG

ORG_DIR = Path(__file__).resolve().parents[1] / "policy_corpus" / "organization"
RAW = "view_warehouse_raw_data"
MASKED = "view_warehouse_masked_data"


def _run(role, query, response=""):
    return apply_governance(response, query, role.lower(), permissions=permissions_for_role(role))


# ── Roles and permissions ────────────────────────────────────────────────────

def test_new_roles_are_catalogued_and_governed():
    for role in ("Data Engineer", "Data Analyst"):
        assert role in ROLE_CATALOG
        assert role in GOVERNANCE_DEMO_ROLES
        assert role in ROLE_PERMISSION_MAP


def test_warehouse_permissions_exist_in_catalog():
    names = {name for name, _category, _description in PERMISSION_CATALOG}
    assert {RAW, MASKED} <= names


def test_raw_warehouse_data_is_data_engineer_only():
    holders = {role for role, perms in ROLE_PERMISSION_MAP.items() if RAW in perms}
    # Admin holds every catalog permission by definition (Access Control
    # Policy §4.10); Data Engineer is the only other role with raw access.
    assert holders == {"Data Engineer", "Admin"}


def test_masked_warehouse_data_is_data_engineer_and_data_analyst():
    holders = {role for role, perms in ROLE_PERMISSION_MAP.items() if MASKED in perms}
    assert holders == {"Data Engineer", "Data Analyst", "Admin"}


def test_data_roles_have_no_hr_data_access():
    for role in ("Data Engineer", "Data Analyst"):
        assert role_has_permission(role, "use_ai_assistant") is True
        assert role_has_permission(role, "view_employee_salary") is False
        assert role_has_permission(role, "view_employee_pii") is False


def test_unmapped_roles_get_no_warehouse_access():
    for role in ("Developer", "Finance", "Analyst"):
        assert role_has_permission(role, RAW) is False
        assert role_has_permission(role, MASKED) is False


# ── Governance decisions ─────────────────────────────────────────────────────

RAW_QUERY = "I need the raw transaction data for yesterday's UPI settlements"
MASKED_QUERY = "Open the masked transaction tables for the lending funnel"


def test_data_engineer_may_request_raw_transaction_data():
    assert _run("Data Engineer", RAW_QUERY).status == "allowed"


@pytest.mark.parametrize("role", ["Data Analyst", "Intern", "Software Engineer", "HR", "Manager", "Supervisor"])
def test_raw_transaction_data_blocked_without_permission(role):
    result = _run(role, RAW_QUERY)
    assert result.status == "blocked"
    assert result.risk_level == "high"
    assert "raw warehouse data" in result.triggered_rules
    assert "Data Warehouse and Analytics Access Policy §4.2" in result.policy_evidence


@pytest.mark.parametrize("role", ["Data Engineer", "Data Analyst"])
def test_masked_tables_allowed_for_data_roles(role):
    assert _run(role, MASKED_QUERY).status == "allowed"


@pytest.mark.parametrize("role", ["Intern", "Software Engineer", "HR", "Manager", "Supervisor"])
def test_masked_tables_blocked_for_everyone_else(role):
    result = _run(role, MASKED_QUERY)
    assert result.status == "blocked"
    assert "warehouse analytics data" in result.triggered_rules
    assert "Data Warehouse and Analytics Access Policy §4.3" in result.policy_evidence


def test_policy_question_about_the_warehouse_is_not_blocked():
    result = _run("Intern", "Who can access raw transaction data under the warehouse policy?")
    assert result.status == "allowed"


def test_data_engineer_still_cannot_get_salary_or_credentials():
    assert _run("Data Engineer", "What is the salary of the analytics lead?").status == "blocked"
    assert _run("Data Engineer", "Send me the warehouse service account password").status == "blocked"


@pytest.mark.parametrize("query,label", [
    ("Read out the Aadhaar of customer 1042", "Aadhaar number"),
    ("What is the PAN number on this loan application?", "PAN details"),
    ("Tell me the CVV for the card ending 4411", "card security code"),
    ("What is the customer's UPI PIN?", "UPI PIN"),
])
def test_identifiers_and_payment_secrets_blocked_for_admin_too(query, label):
    result = _run("Admin", query)
    assert result.status == "blocked"
    assert label in result.triggered_rules
    assert any(c.startswith("Data Classification and Handling Policy §4.") for c in result.policy_evidence)


def test_hr_masking_covers_rupee_amounts():
    result = _run("HR", "When did employee X join?", "They joined in March 2024 on INR 18,75,000 per year.")
    assert result.status == "filtered"
    assert "[AMOUNT REDACTED]" in result.filtered_response
    assert "Data Classification and Handling Policy §4.12" in result.policy_evidence


# ── Citation table <-> policy documents ──────────────────────────────────────

def _all_citations():
    tables = [
        governance._INTERN_RULE_POLICY_MAP,
        governance._THREAT_CATEGORY_POLICY_MAP,
        governance._LAYER2_CATEGORY_POLICY_MAP,
        governance._HR_MASK_POLICY_MAP,
    ]
    return sorted({citation for table in tables for citations in table.values() for citation in citations})


def test_every_enforced_rule_has_a_citation():
    labels = [label for _pattern, label in governance.UNIVERSAL_BLOCKED_RULES]
    labels += [label for _pattern, label, _permission in governance.PERMISSION_GATED_RULES]
    labels += [label for _pattern, label in governance.INTERN_ONLY_CAUTION_RULES]
    for label in labels:
        assert governance._INTERN_RULE_POLICY_MAP.get(label), f"no citation for rule {label!r}"
    for _pattern, _replacement, label in governance.HR_MASKED_RULES:
        assert governance._HR_MASK_POLICY_MAP.get(label), f"no citation for mask {label!r}"
    for category, _keywords in governance.LAYER2_RULE_GROUPS:
        assert governance._LAYER2_CATEGORY_POLICY_MAP.get(category), f"no citation for {category!r}"
    from app.services.threat_detection import CATEGORY_RULES
    for category in CATEGORY_RULES:
        assert governance._THREAT_CATEGORY_POLICY_MAP.get(category), f"no citation for threat {category!r}"


@pytest.mark.parametrize("citation", _all_citations())
def test_citation_points_to_a_real_clause(citation):
    match = re.fullmatch(r"(.+ Policy) §(\d+\.\d+)", citation)
    assert match, f"citation not in '<Document> §N.M' form: {citation!r}"
    title, clause = match.groups()
    path = ORG_DIR / (title.replace(" ", "_") + ".md")
    assert path.exists(), f"{citation!r}: no policy file {path.name}"
    text = path.read_text(encoding="utf-8")
    assert text.startswith(f"# {title}\n"), f"{path.name} title does not match the citation"
    assert re.search(rf"^## {re.escape(clause)} \S", text, re.M), f"{path.name} has no '## {clause}' heading"


def test_permission_matrix_in_access_control_policy_matches_code():
    """The role-to-data matrix in Access Control Policy §4.13 must say the
    same thing as ROLE_PERMISSION_MAP for every governed role."""
    text = (ORG_DIR / "Access_Control_Policy.md").read_text(encoding="utf-8")
    section = text.split("## 4.13 Role-to-data access matrix")[1].split("\n## ")[0]
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in section.splitlines() if line.startswith("|")]
    roles = rows[0][1:]
    table = {row[0]: dict(zip(roles, row[1:])) for row in rows[2:]}
    expected = {
        "Public information": "view_public_information",
        "Use of the SecureAI Assistant": "use_ai_assistant",
        "Project information, full technical view": "view_project_information_full",
        "Employee personal records": "view_employee_pii",
        "Salary and compensation records": "view_employee_salary",
        "Masked analytics tables": MASKED,
        "Raw transaction data": RAW,
        "Audit logs, risk events and governance cases": "ai_governance_admin",
    }
    assert set(roles) == set(GOVERNANCE_DEMO_ROLES)
    for row_name, permission in expected.items():
        for role in roles:
            holds = role_has_permission(role, permission)
            assert table[row_name][role] == ("Yes" if holds else "No"), f"{row_name} / {role}"
    for role in roles:
        limited = role_has_permission(role, "view_project_information_limited") or role_has_permission(role, "view_project_information_full")
        assert table["Project information, limited view"][role] == ("Yes" if limited else "No")


def test_eight_policies_present_and_registered_for_ingestion():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ingest_policies", Path(__file__).resolve().parents[1] / "scripts" / "ingest_policies.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    policy_files = sorted(p.name for p in ORG_DIR.glob("*.md") if p.name not in module.NON_POLICY_FILES)
    assert len(policy_files) == 8
    for name in policy_files:
        assert module.KNOWN_DOCUMENTS[name][1] == "organization"
        text = (ORG_DIR / name).read_text(encoding="utf-8")
        assert "Evolish Technologies Pvt. Ltd." in text
        for heading in ("Purpose", "Scope", "Definitions", "Policy statements", "Roles and responsibilities",
                        "Exceptions", "Enforcement", "Related documents", "Revision history"):
            assert re.search(rf"^## \d+\. {heading}$", text, re.M), f"{name}: missing '## N. {heading}'"
