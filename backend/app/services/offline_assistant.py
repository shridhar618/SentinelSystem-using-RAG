"""
Offline, role-aware answer composer for the policy chatbot.

Used by /api/chat whenever no LLM provider is configured (AI_PROVIDER=mock)
or the configured provider fails. It never invents policy text: answers are
built from

* retrieved policy chunks (semantic RAG results when the Qdrant index is
  available, otherwise a dependency-free keyword/BM25 search over the
  ``policy_chunks`` table), and
* a small, clearly labelled SAMPLE company dataset (projects, employee
  directory, compensation) used to demonstrate that different roles get
  different answers to the same question.

Authorization is still decided by the governance engine
(services/governance.py) -- e.g. an Intern asking for salaries is blocked
there before this text is ever shown. This module additionally scopes what
it *writes* to the caller's permissions (limited vs. full project view,
per-field relevance for PII per Data Privacy Policy §3.3/§4.2), so a
permitted role never receives more than its permission covers.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

from app.services.permissions import PERMISSION_CATALOG

SAMPLE_LABEL = "Sample company data (demo)"

# ── Sample company dataset (fictional) ───────────────────────────────────────

PUBLIC_INFO = {
    "office_hours": "Office hours are 9:30 AM - 6:30 PM, Monday to Friday. Hybrid staff are expected on-site Tuesday to Thursday.",
    "holidays": "The 2026 holiday calendar has 12 company holidays; the full list is published on the HR portal.",
    "support": "IT support is available via the helpdesk portal or ext. 4040. Security incidents go to the Governance Office.",
}

PROJECTS = {
    "atlas": {
        "name": "Project Atlas",
        "limited": {
            "Purpose": "Customer self-service portal redesign",
            "Status": "In progress - phase 2 of 3 (build)",
            "Next milestone": "Beta release on 15 Dec 2026",
            "Team size": "9 members",
        },
        "full": {
            "Architecture": "React SPA -> API gateway -> 4 Flask microservices (accounts, billing, tickets, notifications)",
            "Data stores": "PostgreSQL 16 (primary), Redis (sessions/cache)",
            "Environments": "dev, staging, production (blue/green deploys)",
            "Open technical risks": "Billing service latency under load; legacy SOAP adapter still in the path",
        },
    },
    "beacon": {
        "name": "Project Beacon",
        "limited": {
            "Purpose": "Internal analytics dashboard for operations",
            "Status": "Discovery complete; build starts January 2027",
            "Next milestone": "Architecture sign-off on 10 Jan 2027",
            "Team size": "5 members",
        },
        "full": {
            "Architecture": "Event pipeline (Kafka) -> dbt models -> Superset dashboards",
            "Data stores": "ClickHouse warehouse, S3 raw-event archive",
            "Environments": "staging, production",
            "Open technical risks": "PII must be tokenized before it reaches the warehouse",
        },
    },
}

EMPLOYEES = [
    {"name": "Priya Sharma", "department": "Engineering", "title": "Senior Developer", "work_email": "priya.sharma@secureai.example",
     "work_phone": "+91 80 4000 1101", "joined": "14 Mar 2022", "manager": "Arjun Rao", "salary": "INR 24,00,000 per year"},
    {"name": "Arjun Rao", "department": "Engineering", "title": "Engineering Manager", "work_email": "arjun.rao@secureai.example",
     "work_phone": "+91 80 4000 1102", "joined": "02 Aug 2019", "manager": "Meera Iyer", "salary": "INR 38,50,000 per year"},
    {"name": "Kavya Nair", "department": "Human Resources", "title": "HR Business Partner", "work_email": "kavya.nair@secureai.example",
     "work_phone": "+91 80 4000 1103", "joined": "21 Jun 2021", "manager": "Meera Iyer", "salary": "INR 18,75,000 per year"},
    {"name": "Rohan Das", "department": "Engineering", "title": "Software Engineer Intern", "work_email": "rohan.das@secureai.example",
     "work_phone": "+91 80 4000 1104", "joined": "08 Jul 2026", "manager": "Priya Sharma", "salary": "INR 40,000 per month (stipend)"},
]

# ── Topic detection ──────────────────────────────────────────────────────────

_SALARY_RE = re.compile(r"\b(?:salar(?:y|ies)|compensation|pay\s*scale|payroll|ctc|stipend|how\s+much\s+(?:does|do|is)\b.*\b(?:earn|paid|make))", re.I)
_PII_RE = re.compile(
    r"\b(?:phone|mobile|contact|e-?mail|home\s*address|date\s*of\s*birth|personal\s*(?:data|details|info\w*)|pii|"
    r"employee\s*(?:details|records?|directory|info\w*|list)|joining\s*date|joined|reports?\s+to|who\s+is)\b",
    re.I,
)
_PROJECT_RE = re.compile(r"\b(?:projects?|atlas|beacon|architecture|roadmap|milestones?|tech\s*stack|deploy\w*|environments?|sprint)\b", re.I)
_SELF_ACCESS_RE = re.compile(
    r"\b(?:my\s+(?:role|permissions?|access|rights)|what\s+can\s+i\s+(?:access|see|ask|view|do)|am\s+i\s+allowed|what\s+am\s+i\s+allowed)\b",
    re.I,
)
_PUBLIC_RE = {
    "office_hours": re.compile(r"\b(?:office|working|work)\s*hours?\b|\btimings?\b", re.I),
    "holidays": re.compile(r"\bholidays?\b|\bleave\s+calendar\b", re.I),
    "support": re.compile(r"\b(?:it\s+support|helpdesk|help\s*desk|report\s+an?\s+incident)\b", re.I),
}

_PERMISSION_TEXT = {name: description for name, _category, description in PERMISSION_CATALOG}


@dataclass
class OfflineAnswer:
    text: str
    sources: list = field(default_factory=list)   # [{document_name, section, page, score}]
    scope_limited: bool = False                   # answer trimmed to the role's permission scope
    scope_note: str | None = None
    topic: str = "policy"


# ── Keyword retrieval (fallback when the semantic index is unavailable) ──────

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = set(
    "a an the and or of to in on for with is are was were be been it its this that these those what which who whom how why "
    "when where can could should would do does did i me my we our you your they their there here about as at by from if "
    "into not no yes so than then too very just any all some tell please show give know".split()
)
_ORG_BOOST = 1.6
_chunk_cache: dict = {"key": None, "docs": [], "df": Counter(), "avgdl": 1.0}


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOPWORDS and len(t) > 1]


def _load_chunk_index():
    from app.models.policy_chunk import PolicyChunk
    from app.models.policy_document import PolicyDocument

    rows = (
        PolicyChunk.query.join(PolicyDocument, PolicyChunk.document_id == PolicyDocument.id)
        .filter(PolicyDocument.status == "active")
        .with_entities(PolicyChunk.id, PolicyChunk.content, PolicyChunk.section, PolicyChunk.page,
                       PolicyDocument.name, PolicyDocument.source_type)
        .all()
    )
    key = (len(rows), sum(r[0] for r in rows))
    if _chunk_cache["key"] == key:
        return _chunk_cache
    docs, df = [], Counter()
    for chunk_id, content, section, page, doc_name, source_type in rows:
        toks = _tokens(content)
        if len(toks) < 8:
            continue
        tf = Counter(toks)
        df.update(tf.keys())
        docs.append({
            "id": chunk_id, "content": content, "section": section, "page": page,
            "document_name": doc_name, "org": source_type == "organization", "tf": tf, "len": len(toks),
        })
    _chunk_cache.update(key=key, docs=docs, df=df, avgdl=(sum(d["len"] for d in docs) / len(docs)) if docs else 1.0)
    return _chunk_cache


def keyword_retrieve(query: str, top_k: int = 3) -> list:
    """BM25 over active policy chunks. Same result shape as
    rag_service.retrieve_policy_evidence. Never raises."""
    try:
        index = _load_chunk_index()
    except Exception:
        return []
    q_terms = set(_tokens(query))
    if not q_terms or not index["docs"]:
        return []
    n, avgdl, df = len(index["docs"]), index["avgdl"], index["df"]
    k1, b = 1.4, 0.75
    scored = []
    for doc in index["docs"]:
        score = 0.0
        for term in q_terms:
            freq = doc["tf"].get(term)
            if not freq:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * freq * (k1 + 1) / (freq + k1 * (1 - b + b * doc["len"] / avgdl))
        if score > 0:
            scored.append((score * (_ORG_BOOST if doc["org"] else 1.0), doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    best = scored[0][0] if scored else 0
    results = []
    for score, doc in scored[:top_k]:
        if score < best * 0.45:
            break
        results.append({
            "content": doc["content"], "document_name": doc["document_name"], "section": doc["section"],
            "page": doc["page"], "score": round(score, 2),
        })
    return results


# ── Answer composition ───────────────────────────────────────────────────────

def _clean_excerpt(text: str, limit: int = 480) -> str:
    text = re.sub(r"^#+\s*", "", text or "", flags=re.M)
    text = text.replace("**", "").replace("`", "").replace("|", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[: stop + 1] if stop > limit * 0.5 else cut.rstrip() + "...")


def _role_scope_lines(role_name: str, permissions: list) -> list[str]:
    granted = [_PERMISSION_TEXT[p] for p in permissions if p in _PERMISSION_TEXT]
    denied = [desc for name, desc in _PERMISSION_TEXT.items() if name not in permissions]
    lines = [f"Your role ({role_name}) can: " + "; ".join(granted) + "."]
    if denied:
        lines.append("Not permitted for your role: " + "; ".join(denied[:4]) + ("; ..." if len(denied) > 4 else "") + ".")
    return lines


def _mentioned_employees(query: str) -> list[dict]:
    q = query.lower()
    return [e for e in EMPLOYEES if any(part.lower() in q for part in e["name"].split())]


def _mentioned_projects(query: str) -> list[str]:
    q = query.lower()
    keys = [key for key in PROJECTS if key in q]
    return keys or list(PROJECTS)


def _answer_salary(query, role_name, permissions) -> OfflineAnswer:
    if "view_employee_salary" not in permissions:
        # Normally unreachable: governance blocks this before display.
        return OfflineAnswer(
            text=f"Compensation data is restricted. Your role ({role_name}) does not hold view_employee_salary "
                 "(Role & Access Control Policy §4.1a: only HR and Admin may view compensation).",
            sources=[{"document_name": "Role_and_Access_Control_Policy.md", "section": "4. Principle of Least Privilege"}],
            topic="salary",
        )
    people = _mentioned_employees(query) or EMPLOYEES
    lines = [f"Compensation ({SAMPLE_LABEL}) - shown because your role ({role_name}) holds view_employee_salary:"]
    lines += [f"• {e['name']} ({e['title']}): {e['salary']}" for e in people]
    lines.append("Per Data Privacy Policy §3.4(a), use these figures only for an authorized HR/payroll purpose.")
    return OfflineAnswer(
        text="\n".join(lines),
        sources=[{"document_name": SAMPLE_LABEL, "section": "Payroll"},
                 {"document_name": "Data_Privacy_and_Classification_Policy.md", "section": "3. Handling Requirements by Classification"}],
        topic="salary",
    )


def _answer_pii(query, role_name, permissions) -> OfflineAnswer:
    if "view_employee_pii" not in permissions:
        return OfflineAnswer(
            text=f"Employee personal information is Confidential. Your role ({role_name}) does not hold view_employee_pii "
                 "(Role & Access Control Policy §4.1b: only HR, Manager and Admin may view employee PII).",
            sources=[{"document_name": "Role_and_Access_Control_Policy.md", "section": "4. Principle of Least Privilege"}],
            topic="pii",
        )
    q = query.lower()
    if re.search(r"home\s*address|date\s*of\s*birth", q):
        return OfflineAnswer(
            text="Home addresses and dates of birth are not available through the AI assistant. Request them through the HRIS "
                 "with a documented purpose (Data Privacy Policy §3.3, §4.1).",
            sources=[{"document_name": "Data_Privacy_and_Classification_Policy.md", "section": "4. Response Masking"}],
            topic="pii",
        )
    # Per-field relevance (Data Privacy Policy §3.3 / §4.2): return only what was asked.
    fields = []
    if re.search(r"phone|mobile|contact", q):
        fields.append(("work_phone", "work phone"))
    if re.search(r"e-?mail|contact", q):
        fields.append(("work_email", "work email"))
    if re.search(r"join", q):
        fields.append(("joined", "joined"))
    if re.search(r"manager|reports?\s+to", q):
        fields.append(("manager", "reports to"))
    if not fields:
        fields = [("title", "title"), ("department", "department"), ("work_email", "work email"), ("manager", "reports to")]
    people = _mentioned_employees(query) or EMPLOYEES
    lines = [f"Employee directory ({SAMPLE_LABEL}) - shown because your role ({role_name}) holds view_employee_pii:"]
    for e in people:
        lines.append(f"• {e['name']}: " + ", ".join(f"{label} {e[key]}" for key, label in fields))
    note = None
    if "view_employee_salary" not in permissions:
        note = "Compensation is excluded: your role does not hold view_employee_salary."
        lines.append(note)
    return OfflineAnswer(
        text="\n".join(lines),
        sources=[{"document_name": SAMPLE_LABEL, "section": "Employee directory"},
                 {"document_name": "Data_Privacy_and_Classification_Policy.md", "section": "4. Response Masking"}],
        topic="pii",
    )


def _answer_project(query, role_name, permissions) -> OfflineAnswer:
    full = "view_project_information_full" in permissions
    limited = full or "view_project_information_limited" in permissions
    if not limited:
        return OfflineAnswer(
            text=f"Project information is Internal. Your role ({role_name}) only has public-information access.",
            sources=[{"document_name": "Data_Privacy_and_Classification_Policy.md", "section": "3. Handling Requirements by Classification"}],
            topic="project",
        )
    lines = []
    for key in _mentioned_projects(query):
        project = PROJECTS[key]
        lines.append(f"{project['name']} ({SAMPLE_LABEL}):")
        lines += [f"• {k}: {v}" for k, v in project["limited"].items()]
        if full:
            lines += [f"• {k}: {v}" for k, v in project["full"].items()]
    scope_limited, scope_note = False, None
    asked_technical = bool(re.search(r"architecture|tech\s*stack|deploy|environment|database|data\s*store|technical|risks?", query, re.I))
    if not full:
        scope_note = (f"Technical details (architecture, data stores, environments, technical risks) are withheld: your role "
                      f"({role_name}) holds view_project_information_limited, not view_project_information_full.")
        lines.append(scope_note)
        scope_limited = asked_technical
    else:
        lines.append(f"Full technical view shown because your role ({role_name}) holds view_project_information_full.")
    return OfflineAnswer(
        text="\n".join(lines),
        sources=[{"document_name": SAMPLE_LABEL, "section": "Project register"},
                 {"document_name": "Data_Privacy_and_Classification_Policy.md", "section": "3. Handling Requirements by Classification"}],
        scope_limited=scope_limited,
        scope_note=scope_note if scope_limited else None,
        topic="project",
    )


def _answer_policy(query, role_name, permissions, policy_chunks) -> OfflineAnswer:
    # Prefer the organization's own policies; the NIST/AI RMF PDFs are long
    # and match many generic terms, so they are used only as a fallback.
    candidates = list(policy_chunks or []) + keyword_retrieve(query, top_k=4)
    seen, chunks = set(), []
    for item in sorted(candidates, key=lambda c: 0 if str(c.get("document_name", "")).endswith(".md") else 1):
        key = (item.get("document_name"), item.get("section"), (item.get("content") or "")[:60])
        if key not in seen:
            seen.add(key)
            chunks.append(item)
    if not chunks:
        return OfflineAnswer(
            text="I couldn't find anything relevant in the indexed company policy documents. Please contact the policy owner "
                 "or rephrase the question.\n" + "\n".join(_role_scope_lines(role_name, permissions)),
            topic="policy",
        )
    lines = ["Based on the company policy documents:"]
    sources = []
    for item in chunks[:2]:
        where = item.get("document_name") or "Policy"
        if item.get("section"):
            where += f", {item['section']}"
        if item.get("page"):
            where += f", p. {item['page']}"
        lines.append(f"• [{where}] {_clean_excerpt(item.get('content', ''))}")
    for item in chunks[:3]:
        sources.append({k: item.get(k) for k in ("document_name", "section", "page", "score")})
    lines.append("")
    lines += _role_scope_lines(role_name, permissions)
    return OfflineAnswer(text="\n".join(lines), sources=sources, topic="policy")


def compose_offline_answer(query: str, role_name: str, permissions: list, policy_chunks: list | None = None,
                           llm_configured: bool = False) -> OfflineAnswer:
    """Build a role-scoped answer without an LLM."""
    from app.services.governance import is_policy_question

    q = query or ""
    if _SELF_ACCESS_RE.search(q):
        answer = OfflineAnswer(
            text="\n".join(_role_scope_lines(role_name, permissions))
            + "\nSource: Role & Access Control Policy §3 (role definitions).",
            sources=[{"document_name": "Role_and_Access_Control_Policy.md", "section": "3. Role Definitions"}],
            topic="access",
        )
    elif is_policy_question(q):
        answer = _answer_policy(q, role_name, permissions, policy_chunks)
    elif _SALARY_RE.search(q):
        answer = _answer_salary(q, role_name, permissions)
    elif _PII_RE.search(q) and (_mentioned_employees(q) or re.search(r"employee|staff|directory|contact|phone|e-?mail|pii|personal|address|birth", q, re.I)):
        answer = _answer_pii(q, role_name, permissions)
    elif _PROJECT_RE.search(q) and not re.search(r"\bpolic(?:y|ies)\b", q, re.I):
        answer = _answer_project(q, role_name, permissions)
    else:
        public_key = next((key for key, rx in _PUBLIC_RE.items() if rx.search(q)), None)
        if public_key:
            answer = OfflineAnswer(text=f"{PUBLIC_INFO[public_key]} ({SAMPLE_LABEL}; public information)",
                                   sources=[{"document_name": SAMPLE_LABEL, "section": "Public information"}], topic="public")
        else:
            answer = _answer_policy(q, role_name, permissions, policy_chunks)
    if not llm_configured:
        answer.text = "[Offline policy mode - no LLM configured]\n" + answer.text
    return answer


# ── Startup seeding of policy text (no ML dependencies) ──────────────────────

_ORG_POLICY_CATEGORIES = {
    "AI_Acceptable_Use_Policy.md": "Acceptable Use",
    "Role_and_Access_Control_Policy.md": "Access Control",
    "Data_Privacy_and_Classification_Policy.md": "Privacy",
    "AI_Security_and_Incident_Response_Policy.md": "Security",
}
_SEED_CHUNK_SIZE = 800
_SEED_CHUNK_OVERLAP = 120


def _seed_chunks(text: str) -> list[str]:
    """Same fallback splitter as scripts/ingest_policies.py."""
    chunks, start = [], 0
    while start < len(text):
        end = min(start + _SEED_CHUNK_SIZE, len(text))
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        start = end - _SEED_CHUNK_OVERLAP if end - _SEED_CHUNK_OVERLAP > start else end
    return chunks


def seed_policy_text_if_empty() -> int:
    """On a fresh database (e.g. a new cloud deploy without a persistent
    disk), load the organization policy documents into policy_chunks so the
    offline assistant can answer policy questions. Text only -- semantic
    vectors still come from scripts/ingest_policies.py when RAG is installed.
    Returns the number of chunks created (0 if chunks already exist)."""
    from datetime import UTC, datetime
    from pathlib import Path

    from app import db
    from app.models.policy_chunk import PolicyChunk
    from app.models.policy_document import PolicyDocument

    if PolicyChunk.query.first() is not None:
        return 0
    org_dir = Path(__file__).resolve().parents[2] / "policy_corpus" / "organization"
    created = 0
    for name, category in _ORG_POLICY_CATEGORIES.items():
        path = org_dir / name
        if not path.exists():
            continue
        doc = PolicyDocument.query.filter_by(name=name).first()
        if doc is None:
            doc = PolicyDocument(name=name, category=category, source_type="organization", file_path=str(path))
            db.session.add(doc)
            db.session.flush()
        index = 0
        for part in re.split(r"\n(?=## )", path.read_text(encoding="utf-8")):
            header = re.match(r"##\s*(.+)", part)
            section = header.group(1).strip() if header else "Preamble"
            cleaned = re.sub(r"\s+", " ", part).strip()
            for piece in _seed_chunks(cleaned) if cleaned else []:
                db.session.add(PolicyChunk(document_id=doc.id, chunk_index=index, content=piece, section=section))
                index += 1
        doc.chunk_count = index
        doc.last_indexed_at = datetime.now(UTC)
        created += index
    db.session.commit()
    return created
