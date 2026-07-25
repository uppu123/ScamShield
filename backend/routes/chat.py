import re

from flask import Blueprint, jsonify, request

bp = Blueprint("chat", __name__)

FAQS = [
    (
        [r"registration\s*fee", r"processing\s*fee", r"pay\s+to\s+apply", r"pay\s+money", r"transfer\s+money"],
        "Legitimate employers never ask candidates to pay any fee — registration, processing, security, or otherwise. If a posting asks you to pay before you get paid, that is a strong scam signal. Do not pay.",
    ),
    (
        [r"security\s*deposit", r"refundable\s*deposit", r"deposit"],
        "A 'security' or 'refundable' deposit is a classic scam tactic. Real employers do not ask for deposits from job seekers to 'book a seat' or 'activate an account'.",
    ),
    (
        [r"salary", r"50000", r"50,000", r"too\s+good", r"guaranteed"],
        "Salaries far above the market rate for entry-level or work-from-home roles — especially 'guaranteed' income — are a red flag. Cross-check the same role at similar companies and on the company's official careers page.",
    ),
    (
        [r"whatsapp", r"gmail", r"@yahoo", r"@hotmail", r"personal\s*contact"],
        "Scammers often route you to a personal WhatsApp number or a free Gmail address instead of an official company-domain email. Verify the recruiter's email domain and the company's real website.",
    ),
    (
        [r"is\s+this\s+legit", r"legitimate", r"genuine", r"real", r"safe", r"trust"],
        "To verify: 1) find the company's official website and careers page, 2) confirm the recruiter email uses the company domain, 3) never pay any fee, 4) check for the posting on LinkedIn/company channels, 5) be suspicious of urgency and too-good salaries.",
    ),
    (
        [r"urgent", r"limited\s*seats", r"apply\s*within", r"hurry"],
        "Urgency is used to stop you from verifying the posting. Real employers rarely pressure you to apply 'within hours' or pay to 'reserve a seat'. Slow down and verify first.",
    ),
    (
        [r"work\s+from\s+home", r"data\s*entry", r"typing"],
        "Work-from-home / data-entry / typing jobs with high salaries and no skill requirements are frequently scams, especially when combined with a fee or a personal contact. Treat them with extra caution.",
    ),
]

DEFAULT_ANSWER = (
    "I can help you evaluate a job posting. Paste the text into the Analyze tab. As a general rule: "
    "never pay any fee, verify the recruiter's company-domain email, check the company's official "
    "careers page, and be wary of urgency and too-good-to-be-true salaries."
)


def _answer(message):
    lowered = message.lower()
    for patterns, answer in FAQS:
        if any(re.search(pattern, lowered) for pattern in patterns):
            return answer
    return DEFAULT_ANSWER


@bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty_message"}), 400
    return jsonify({"message": message, "reply": _answer(message)})
