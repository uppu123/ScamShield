"""In-process client for the single-container Streamlit Cloud deployment.

Replaces HTTP calls to the Flask backend with direct in-process calls, so the
whole app runs as ONE process on Streamlit Community Cloud (free tier). It
mirrors the Flask route response shapes so the frontend components stay
unchanged.

Secrets come from `.streamlit/secrets.toml` (Streamlit Cloud) or the repo-root
`.env` file (local dev). Available secret keys: MONGO_URI, GEMINI_API_KEY,
TESSERACT_CMD, SCAMSHIELD_MODEL, SCAMSHIELD_DISABLE_MODEL.

NOTE: module import is side-effect free (no Streamlit commands enqueued) so the
app can call `st.set_page_config` first. Secrets and DB are configured lazily
on the first call.
"""

import hashlib
import os
import sys
from datetime import datetime, timezone

import streamlit as st

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

_SECRET_KEYS = (
    "MONGO_URI",
    "GEMINI_API_KEY",
    "TESSERACT_CMD",
    "SCAMSHIELD_MODEL",
    "SCAMSHIELD_DISABLE_MODEL",
)

_configured = False
db = None


def _configure():
    global _configured, db
    if _configured:
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(REPO_ROOT, ".env"))
    except Exception:
        pass
    try:
        secrets = st.secrets
        if secrets.load_if_toml_exists():
            for key in _SECRET_KEYS:
                try:
                    value = secrets.get(key, "")
                    if value:
                        os.environ.setdefault(key, str(value))
                except Exception:
                    pass
    except Exception:
        pass
    from backend.db.mongo import db as _db
    db = _db
    _configured = True


from backend.chat_service import _answer, _llm_reply  # noqa: E402
from backend.core.pipeline import ScamPipeline  # noqa: E402


def _model_ref():
    if os.environ.get("SCAMSHIELD_DISABLE_MODEL"):
        return None
    explicit = (os.environ.get("SCAMSHIELD_MODEL") or "").strip()
    if explicit:
        return None if explicit.lower() == "off" else explicit
    local = os.path.join(REPO_ROOT, "artifacts", "model")
    if os.path.isdir(local):
        return local
    return "nimoAlpha/scamshield-distilbert"


@st.cache_resource(show_spinner=False)
def _pipeline():
    return ScamPipeline({"model_dir": _model_ref(), "dup_threshold": 0.8})


def health():
    return True


def analyze_text(text):
    _configure()
    result = _pipeline().analyze_text(text)
    if result.get("error"):
        return result
    result["type"] = "text"
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["hash"] = hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]
    if db.is_connected():
        db.insert_posting(result)
    return result


def analyze_image(image_bytes):
    _configure()
    result = _pipeline().analyze_image(image_bytes)
    if result.get("error"):
        return result
    result["type"] = "image"
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["hash"] = hashlib.sha256(image_bytes).hexdigest()[:16]
    if db.is_connected():
        db.insert_posting(result)
    return result


def chat(message, history=None):
    _configure()
    reply = _llm_reply(history or [], message)
    if reply:
        return {"message": message, "reply": reply, "source": "llm"}
    return {"message": message, "reply": _answer(message), "source": "faq"}


def report_scam(text, notes="", source="unknown", contact=""):
    _configure()
    text = (text or "").strip()
    if not text:
        return {"error": "empty_text", "message": "Provide the scam posting text."}
    report = {
        "text": text,
        "notes": notes,
        "source": source,
        "contact": contact,
        "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if db.is_connected():
        db.insert_report(report)
        return {"status": "saved", "report": report}
    return {"status": "offline", "message": "Reports DB not configured; nothing stored."}


def recent_reports(limit=15):
    _configure()
    limit = max(1, min(int(limit), 50))
    return {"reports": db.recent_reports(limit)}
