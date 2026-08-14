"""Chat logic for ScamShield, framework-agnostic so it can be called from
both the Flask API routes and the single-process Streamlit Cloud app."""

import os
import re

SYSTEM_PROMPT = (
    "You are ScamShield Assistant, the chat helper for ScamShield, a fake job-posting and "
    "recruitment-fraud detector built for the Indian job market. You answer questions about job "
    "scams, verifying recruiters and companies, red flags, upfront fee and deposit tricks, "
    "WhatsApp/Gmail recruitment fraud, fake work-from-home or data-entry jobs, and safe job-search "
    "practices.\n\n"
    "Rules:\n"
    "1) Answer clearly and concisely, in plain language; Markdown bullets are fine. Keep answers "
    "under ~150 words unless the user asks for more depth.\n"
    "2) Always steer toward safe practices: never pay money to get a job, verify the company's "
    "official website and careers page, confirm the recruiter's email uses the company's own domain, "
    "and be wary of urgency, too-good-to-be-true salaries, and requests for personal or financial "
    "details.\n"
    "3) If the user pastes a job posting and asks 'is this a scam', point out any suspicious patterns "
    "(fees, deposits, generic Gmail/WhatsApp/phone contacts, unrealistic pay for unskilled work, "
    "urgency) and give a balanced verdict, noting it is guidance, not proof.\n"
    "4) If the user asks something unrelated to job scams or recruitment fraud, politely redirect "
    "them back to the topic.\n"
    "5) You are part of a conversation, so remember what was said earlier in the conversation and "
    "answer follow-up questions in context.\n"
)

MODEL_CANDIDATES = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]

_model_name = {"value": None}


def _llm_reply(prior_history, message):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=600,
            temperature=0.4,
        )
        contents = []
        for item in prior_history[-12:]:
            role = "model" if item.get("role") == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=item.get("content", ""))]))
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

        candidates = [_model_name["value"]] if _model_name["value"] else MODEL_CANDIDATES
        for name in candidates:
            try:
                response = client.models.generate_content(model=name, contents=contents, config=config)
                text = (response.text or "").strip()
                if text:
                    _model_name["value"] = name
                    return text
            except Exception:
                continue
    except Exception:
        pass
    return None


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
