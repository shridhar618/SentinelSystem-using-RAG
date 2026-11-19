"""
Contextual threat detection for the AI chatbot (Interactive Ghost Mode).

The governance engine (services/governance.py) decides what a *response*
may contain. This module answers a different question: does the *intent*
of an incoming message look like an attempt to attack the platform or other
users? It produces a 0-100 threat score, a level, and the categories and
signals that explain the score, so an administrator can see *why* a
message was flagged.

Design notes
------------
* Context over keywords. A category only fires on attack-shaped phrasing
  (e.g. "give me the admin password", not merely "password"), and the
  score is then adjusted by intent markers:
    - malicious markers (acquisition verbs aimed at other people's data,
      "without permission", "undetected", targeting admin/root) raise it;
    - educational markers ("what is", "explain", "how do I prevent",
      "best practices", coursework) dampen it heavily, so ordinary
      cybersecurity study questions stay LOW and never raise an alert.
* Deterministic and DB-free, so it is directly unit-testable and cheap
  enough to run on every chat message.
"""

import re
from dataclasses import dataclass, field

LEVEL_BANDS = [  # (exclusive upper bound, level)
    (30, "low"),
    (55, "medium"),
    (80, "high"),
    (101, "critical"),
]

DEFAULT_ALERT_THRESHOLD = 50

CATEGORY_LABELS = {
    "unauthorized_access": "Unauthorized access attempt",
    "private_conversation_access": "Private conversation access",
    "credential_theft": "Credential theft",
    "database_exploitation": "Database exploitation",
    "auth_bypass": "Authentication bypass",
    "sensitive_data_extraction": "Sensitive data extraction",
    "privilege_escalation": "Privilege escalation",
    "prompt_injection": "Prompt injection / jailbreak",
}

_ACQUIRE = r"(?:give|show|send|share|tell|reveal|leak|list|print|display|get|grab|fetch|retrieve|obtain|steal|harvest|extract|pull|find|access|read|see|view|open|dump|export)"
_OTHERS = r"(?:other|another|every|all|someone(?:\s+else)?|anyone|any)\s*(?:'s\s+)?(?:user|student|employee|member|staff|person|people|account|admin)?s?'?s?"

# category -> (base weight, [patterns])
CATEGORY_RULES = {
    "credential_theft": (50, [
        rf"\b{_ACQUIRE}\b[^.?!\n]{{0,50}}\b(?:passwords?|passwd|passcodes?|credentials?|login\s*(?:code|details|info)|api[\s_-]?keys?|access\s*tokens?|session\s*(?:tokens?|cookies?)|jwt|secret\s*keys?|password\s*hash(?:es)?|private\s*keys?)\b",
        r"\b(?:password|credentials?|login\s*code|token)s?\s+(?:of|for|belonging\s+to)\s+(?:the\s+)?(?:admin|administrator|root|user|student|employee|everyone|all|other|another|[a-z]+_[a-z]+)",
        r"\b(?:admin|administrator|root|superuser)(?:'s)?\s+(?:password|credentials?|login|token)",
        r"\b(?:crack|brute[\s-]?force|bruteforce)\b[^.?!\n]{0,40}\b(?:password|hash|login|account)",
        r"\b(?:phish|keylog|credential\s*(?:dump|stuff)|password\s*(?:dump|spray)|mimikatz)",
    ]),
    "private_conversation_access": (50, [
        rf"\b{_ACQUIRE}\b[^.?!\n]{{0,50}}\b(?:private|personal|direct|someone(?:\s+else)?'?s?|other\s+(?:users?|students?|people)'?s?|their)\s+(?:chats?|messages?|conversations?|dms?|inbox|emails?|history)",
        r"\b(?:chats?|messages?|conversations?|dms?|inbox|chat\s*history)\s+(?:of|from|between|belonging\s+to)\s+(?:other|another|all|every|the\s+admin|[a-z]+_[a-z]+|[A-Z][a-z]+)",
        r"\b(?:read|spy\s+on|monitor|intercept|snoop\s+on|eavesdrop\s+on)\b[^.?!\n]{0,40}\b(?:chats?|messages?|conversations?|dms?)",
        r"\b[A-Z][a-z]+'s\s+(?:private\s+)?(?:chats?|messages?|conversations?|dms?)\b",
    ]),
    "database_exploitation": (48, [
        r"\b(?:dump|drop|truncate|exfiltrate|export)\b[^.?!\n]{0,30}\b(?:database|db|tables?|users?\s*table|schema|records)\b",
        r"(?:'\s*or\s*'?1'?\s*=\s*'?1|\bunion\s+select\b|;\s*drop\s+table|--\s*$|\bor\s+1\s*=\s*1\b)",
        r"\bselect\s+\*\s+from\s+\w+",
        r"\b(?:run|execute|inject)\b[^.?!\n]{0,30}\b(?:sql|query|queries|command)s?\b[^.?!\n]{0,30}\b(?:database|db|server|backend|your)",
        r"\bsql\s*injection\b[^.?!\n]{0,40}\b(?:this|your|the)\s+(?:app|site|system|database|login|platform|server)",
        r"\b(?:sqlmap|shadow\s+file|/etc/passwd|/etc/shadow)\b",
    ]),
    "auth_bypass": (50, [
        r"\b(?:bypass|circumvent|skip|get\s+around|evade|disable|defeat|break)\b[^.?!\n]{0,40}\b(?:login|log\s*in|auth\w*|2fa|mfa|otp|verification|captcha|face\s*(?:unlock|recognition)|password\s*check|session|security)",
        r"\b(?:forge|fake|tamper\s+with|modify|reuse|replay|hijack|steal)\b[^.?!\n]{0,30}\b(?:jwt|token|session|cookie)s?\b",
        r"\b(?:log\s*in|sign\s*in|get\s+in(?:to)?)\b[^.?!\n]{0,30}\b(?:without\s+(?:a\s+|the\s+)?(?:password|credentials|permission|authori[sz]ation|login\s*code))",
        r"\bimpersonat\w*\b[^.?!\n]{0,30}\b(?:user|admin|student|someone|account)",
    ]),
    "unauthorized_access": (45, [
        rf"\b(?:access|get\s+into|break\s+into|hack\s+into|hack|log\s*into|enter|take\s+over|control)\b[^.?!\n]{{0,30}}\b{_OTHERS}\s*(?:accounts?|profiles?|data|files?|records?|dashboard)",
        r"\b(?:hack|break\s+into|take\s+over|compromise|hijack)\b[^.?!\n]{0,30}\b(?:account|system|server|portal|platform|admin\s*panel|dashboard)",
        r"\b(?:access|open|get\s+into)\b[^.?!\n]{0,30}\b(?:admin\s*(?:panel|dashboard|page|console|area)|restricted\s+(?:area|page|section|files?|data))",
        r"\bunauthori[sz]ed\s+access\b[^.?!\n]{0,30}\b(?:to|into)\b",
        r"\b(?:exploit|attack|hack|pwn|ddos|breach|crash|take\s+down)\b[^.?!\n]{0,30}\b(?:login|server|website|site|web\s*app|app|application|portal|system|network|database|api|endpoint|admin)\b",
    ]),
    "sensitive_data_extraction": (45, [
        rf"\b{_ACQUIRE}\b[^.?!\n]{{0,50}}\b(?:all|every|full|complete|entire|bulk)\b[^.?!\n]{{0,30}}\b(?:users?|students?|employees?|records?|grades?|marks|emails?|phone\s*numbers?|addresses|salar(?:y|ies)|ssns?|personal\s*(?:data|info\w*|details)|pii)",
        rf"\b{_ACQUIRE}\b[^.?!\n]{{0,40}}\b(?:ssn|social\s*security|credit\s*card|bank\s*account|date\s*of\s*birth|home\s*address|medical\s*records?|grades?|marks|salary)\b[^.?!\n]{{0,30}}\b(?:of|for)\s+\w+",
        r"\b(?:exfiltrat\w*|scrape|harvest|mass[\s-]?download)\b",
        r"\b(?:list|export|download)\s+(?:all|every)\s+(?:users?|students?|employees?|accounts?)",
    ]),
    "privilege_escalation": (50, [
        r"\b(?:make|set|promote|grant|give|upgrade|change|elevate|escalate)\b[^.?!\n]{0,30}\b(?:me|my\s+(?:account|role|user)|myself)\b[^.?!\n]{0,30}\b(?:admin|administrator|root|superuser|sudo|elevated|full\s+access|privileges?|permissions?)",
        r"\b(?:escalate|elevate)\s+(?:my\s+)?(?:privileges?|permissions?|access|role)",
        r"\b(?:change|switch|modify|set)\s+my\s+role\b",
        r"\b(?:sudo|root)\s+access\b",
        r"\b(?:give|grant)\s+me\s+(?:admin|full|root|elevated|unrestricted)\s+(?:access|rights|privileges?|permissions?)",
    ]),
    "prompt_injection": (40, [
        r"\bignore\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|earlier|your)\s+(?:instructions?|rules|prompts?|guidelines?)",
        r"\b(?:reveal|show|print|repeat|output)\b[^.?!\n]{0,20}\b(?:your\s+)?(?:system\s+prompt|hidden\s+(?:prompt|instructions?)|initial\s+instructions?)",
        r"\byou\s+are\s+now\b[^.?!\n]{0,40}\b(?:unrestricted|unfiltered|jailbroken|dan|developer\s+mode|without\s+(?:rules|restrictions|filters))",
        r"\b(?:developer|god|admin|debug)\s+mode\s+(?:on|enabled|activated)\b",
        r"\b(?:jailbreak|do\s+anything\s+now)\b",
        r"\bpretend\s+(?:you\s+(?:are|have)|to\s+be)\b[^.?!\n]{0,40}\b(?:no\s+(?:rules|restrictions|filters)|admin|root|unrestricted)",
    ]),
}

# Raise the score: aimed at other people / admin assets, or explicitly covert.
MALICIOUS_MARKERS = [
    (r"\bwithout\s+(?:them|him|her|their|anyone)\s+(?:knowing|noticing|finding\s+out)", "covert intent"),
    (r"\bwithout\s+(?:permission|authori[sz]ation|consent|being\s+(?:detected|caught|logged|noticed))", "acting without authorization"),
    (r"\b(?:undetected|cover\s+(?:my|our)\s+tracks|delete\s+(?:the\s+)?logs|clear\s+(?:the\s+)?(?:audit|logs)|disable\s+(?:logging|monitoring))", "evasion of monitoring"),
    (rf"\b{_OTHERS}\s*(?:accounts?|passwords?|messages?|chats?|data|records?|grades?)", "targets other users' data"),
    (r"\b(?:admin|administrator|root|superuser)(?:'s)?\s+(?:account|password|credentials?|access|panel|privileges?|token)", "targets administrator assets"),
    (r"\b(?:right\s+now|immediately|asap)\b", "urgency pressure"),
    (r"\b(?:give|show|send|tell|reveal|dump)\s+me\b", "direct acquisition request"),
    (r"\bi\s+(?:need|want)\s+(?:to\s+)?(?:get\s+)?(?:access|into|the\s+password|their|his|her)", "stated acquisition goal"),
]

# Dampen the score: study, defence, and how-it-works phrasing.
EDUCATIONAL_MARKERS = [
    r"^\s*(?:what|why)\s+(?:is|are|was|were|does|do)\b",
    r"^\s*(?:can|could)\s+you\s+explain\b",
    r"\bexplain\b",
    r"\bhow\s+(?:does|do|did|is|are)\b[^.?!\n]{0,60}\b(?:work|happen|function|operate)",
    r"\b(?:prevent|prevention|protect|protection|defend|defen[cs]e|mitigat\w*|detect|detection|secure\s+(?:against|my|our)|harden|patch|safeguard|avoid|recogni[sz]e)\b",
    r"\b(?:best\s+practices?|awareness|course|class|exam|assignment|homework|lecture|study|studying|learn|learning|tutorial|definition|define|difference\s+between|example\s+of|overview|concept|theory|history\s+of)\b",
    r"\b(?:policy|policies|guideline|guidelines|rules?\s+for|requirements?\s+for)\b",
    r"\b(?:i\s+forgot|reset\s+my|recover\s+my|my\s+own)\s+(?:password|account|login)",
]

# A message with no attack category can still carry a weak signal.
WEAK_SIGNALS = [
    (r"\b(?:hack|exploit|backdoor|payload|rootkit|keylogger|reverse\s+shell)\b", 12, "attack vocabulary"),
    (r"\b(?:admin\s+panel|admin\s+password|root\s+password)\b", 10, "admin asset mention"),
]


@dataclass
class ThreatAssessment:
    score: int = 0
    level: str = "low"
    category: str | None = None
    categories: list = field(default_factory=list)
    signals: list = field(default_factory=list)
    educational: bool = False

    @property
    def category_label(self):
        return CATEGORY_LABELS.get(self.category, "Suspicious activity") if self.category else "None"

    def to_dict(self):
        return {
            "score": self.score,
            "level": self.level,
            "category": self.category,
            "category_label": self.category_label,
            "categories": self.categories,
            "signals": self.signals,
            "educational": self.educational,
        }


def score_to_level(score: int) -> str:
    for upper, level in LEVEL_BANDS:
        if score < upper:
            return level
    return "critical"


def analyze_message(message: str) -> ThreatAssessment:
    """Score one chat message for malicious intent (0-100)."""
    text = (message or "").strip()
    if not text:
        return ThreatAssessment()
    lowered = text.lower()

    hits = []  # (weight, category, matched snippet)
    for category, (weight, patterns) in CATEGORY_RULES.items():
        for pattern in patterns:
            # Some patterns rely on capitalisation (names), so match both.
            match = re.search(pattern, lowered, re.IGNORECASE) or re.search(pattern, text)
            if match:
                hits.append((weight, category, match.group(0).strip()[:80]))
                break

    signals = [f"{CATEGORY_LABELS[c]}: “{snippet}”" for _w, c, snippet in hits]

    if hits:
        hits.sort(key=lambda item: item[0], reverse=True)
        score = float(hits[0][0])
        # Additional categories add with diminishing returns.
        score += sum(weight * 0.35 for weight, _c, _s in hits[1:])
    else:
        score = 0.0
        for pattern, weight, label in WEAK_SIGNALS:
            if re.search(pattern, lowered):
                score += weight
                signals.append(f"Weak signal: {label}")

    malicious_hits = []
    for pattern, label in MALICIOUS_MARKERS:
        if re.search(pattern, lowered):
            malicious_hits.append(label)
    if malicious_hits and (hits or score > 0):
        score += min(36, 12 * len(malicious_hits))
        signals.extend(f"Intent marker: {label}" for label in malicious_hits)

    educational = any(re.search(pattern, lowered) for pattern in EDUCATIONAL_MARKERS)
    if educational:
        # Strong covert/targeting intent survives an "explain" prefix
        # ("explain how to read Priya's messages without her knowing");
        # plain study questions do not.
        strong_intent = any(
            label in {"covert intent", "acting without authorization", "evasion of monitoring", "targets other users' data"}
            for label in malicious_hits
        )
        score *= 0.75 if strong_intent else 0.3
        signals.append("Educational / defensive framing detected" + (" (overridden by targeting intent)" if strong_intent else ""))

    final = int(round(max(0.0, min(100.0, score))))
    categories = []
    for _w, category, _s in hits:
        if category not in categories:
            categories.append(category)
    return ThreatAssessment(
        score=final,
        level=score_to_level(final),
        category=categories[0] if categories else None,
        categories=categories,
        signals=signals,
        educational=educational,
    )


def load_alert_threshold() -> int:
    """Admin-configurable via the existing RiskConfiguration table
    (key `ghost_threat_alert_threshold`, editable on the risk config page)."""
    try:
        from app.models.risk_configuration import RiskConfiguration

        row = RiskConfiguration.query.filter_by(key="ghost_threat_alert_threshold", enabled=True).first()
        if row is not None and row.value is not None:
            return int(max(1, min(100, round(row.value))))
    except Exception:  # pragma: no cover - DB unavailable
        pass
    return DEFAULT_ALERT_THRESHOLD
