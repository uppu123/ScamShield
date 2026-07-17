import re

EMAIL_GENERIC = re.compile(
    r"\b[\w.+-]+@(?:gmail|yahoo|hotmail|outlook|rediffmail|live|aol|protonmail|zoho|icloud)\.(?:com|in|co\.in|org|net)\b",
    re.I,
)
EMAIL_ANY = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.I)
PHONE = re.compile(r"\b(?:\+?91[-.\s]?)?[6-9]\d{9}\b")
WHATSAPP = re.compile(r"\b(?:whatsapp|wtsapp|wa\.me)\b", re.I)

FEE_PATTERNS = [
    re.compile(r"\b(?:registration|processing|application|candidate|joining)\s*(?:fee|charges?|amount)\b", re.I),
    re.compile(r"\b(?:pay|paying|transfer|send)\s*(?:a\s+|the\s+|any\s+)?(?:registration|processing|application|candidate)\s*(?:fee|charges?|amount)?\b", re.I),
    re.compile(r"\b(?:security|refundable|cash)\s+deposit\b", re.I),
    re.compile(r"\bpay\s+to\s+apply\b", re.I),
    re.compile(r"\bdeposit\s+(?:money|amount|fee)\b", re.I),
]

URGENCY_PATTERNS = [
    re.compile(r"\bapply\s+(?:within|before|immediately)\b", re.I),
    re.compile(r"\b(?:hurry|urgent(?:ly)?|asap|immediate\s+joining)\b", re.I),
    re.compile(r"\blimited\s+(?:seats?|positions?|slots?|vacancies?)\b", re.I),
    re.compile(r"\bonly\s+\d+\s*(?:hours?|days?)\s*(?:left|remaining)?\b", re.I),
    re.compile(r"\blast\s+(?:chance|call|date|seats?)\b", re.I),
]

HIGH_AMOUNT = re.compile(r"(?:rs\.?|inr|₹)\s?[3-9][\d,]{5,}\b", re.I)
ENTRY_LEVEL = re.compile(
    r"\b(?:no\s+experience|freshers?|entry\s+level|no\s+skills?\s+required)\b"
    r"|\b(?:typing|data\s+entry|copy\s+paste|online\s+form\s+filling)\b",
    re.I,
)
WORK_FROM_HOME = re.compile(r"\b(?:work\s+from\s+home|work\s+at\s+home|wfh)\b", re.I)

TOO_GOOD_PATTERNS = [
    re.compile(r"\bguaranteed\s+(?:income|salary|payout|earnings|monthly\s+income)\b", re.I),
    re.compile(r"\b(?:earn|earning|income|salary)\b.{0,60}\b(?:per|every|each)\s+(?:day|week)\b", re.I),
    re.compile(r"\b(?:no\s+experience|freshers?|entry\s+level)\b.{0,80}\b(?:rs\.?|inr|₹)\s?[\d,]{6,}\b", re.I),
    re.compile(r"\b(?:work\s+from\s+home|work\s+at\s+home|wfh)\b.{0,80}\b(?:rs\.?|inr|₹)\s?[\d,]{6,}\b", re.I),
]


def _matches(patterns, text, limit=3):
    evidence = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            snippet = match.group(0).strip()
            if snippet and snippet not in evidence:
                evidence.append(snippet)
            if len(evidence) >= limit:
                return evidence
    return evidence


def _check_fee(text):
    return _matches(FEE_PATTERNS, text)


def _check_urgency(text):
    return _matches(URGENCY_PATTERNS, text)


def _check_generic_contact(text):
    generic_emails = [m.group(0) for m in EMAIL_GENERIC.finditer(text)]
    has_company_email = bool(EMAIL_ANY.search(text))
    if generic_emails:
        return generic_emails
    if WHATSAPP.search(text):
        return ["whatsapp contact provided"]
    if PHONE.search(text) and not has_company_email:
        return [m.group(0) for m in PHONE.finditer(text)][:3]
    return []


def _check_missing_company(text):
    if EMAIL_ANY.search(text) or PHONE.search(text) or WHATSAPP.search(text):
        return []
    return ["no employer contact details found"]


def _check_salary_anomaly(text):
    high = [m.group(0) for m in HIGH_AMOUNT.finditer(text)]
    if not high:
        return []
    if ENTRY_LEVEL.search(text) or WORK_FROM_HOME.search(text):
        return high[:3]
    return []


def _check_too_good(text):
    return _matches(TOO_GOOD_PATTERNS, text)


BUILTIN_RULES = [
    {
        "id": "fee_request",
        "name": "Upfront fee requested",
        "severity": 1.0,
        "explanation": "The posting asks you to pay a fee or deposit. Legitimate employers never charge job seekers.",
        "check": _check_fee,
    },
    {
        "id": "too_good_to_be_true",
        "name": "Too-good-to-be-true pay",
        "severity": 0.9,
        "explanation": "Unrealistic income promises (guaranteed pay, per-day/week pay, huge salaries for unskilled or work-from-home roles) are a classic scam pattern.",
        "check": _check_too_good,
    },
    {
        "id": "generic_contact",
        "name": "Generic contact instead of company domain",
        "severity": 0.8,
        "explanation": "Contact details use a free email provider or personal WhatsApp/phone instead of an official company domain.",
        "check": _check_generic_contact,
    },
    {
        "id": "salary_anomaly",
        "name": "Salary-to-role mismatch",
        "severity": 0.7,
        "explanation": "A high salary is offered for an entry-level or work-from-home role with no skills required.",
        "check": _check_salary_anomaly,
    },
    {
        "id": "missing_company_details",
        "name": "Missing company details",
        "severity": 0.6,
        "explanation": "The posting includes no company contact details (email/phone), so it cannot be verified.",
        "check": _check_missing_company,
    },
    {
        "id": "urgency_pressure",
        "name": "Urgency / pressure tactics",
        "severity": 0.5,
        "explanation": "The posting pressures you to act fast (limited seats, apply within hours) to prevent you from verifying it.",
        "check": _check_urgency,
    },
]


class RuleHit:
    def __init__(self, rule_id, name, severity, explanation, evidence):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
        self.explanation = explanation
        self.evidence = evidence

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "severity": self.severity,
            "explanation": self.explanation,
            "evidence": self.evidence,
        }


class RuleEngine:
    def __init__(self, rules=None):
        self.rules = rules or BUILTIN_RULES

    def analyze(self, text):
        if not (text or "").strip():
            return []
        hits = []
        for rule in self.rules:
            evidence = rule["check"](text)
            if evidence:
                hits.append(
                    RuleHit(
                        rule["id"], rule["name"], rule["severity"], rule["explanation"], evidence
                    )
                )
        return hits

    def score(self, hits):
        if not hits:
            return 0.0
        return min(sum(h.severity for h in hits) / len(self.rules), 1.0)
