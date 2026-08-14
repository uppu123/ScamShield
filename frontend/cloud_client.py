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
from collections.abc import Mapping
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
_config_error = None
db = None


def _find_secret(secrets, key, depth=0):
    """Look up a secret by exact key, searching nested sections too.

    Covers dashboard secrets stored at the top level (recommended) or under a
    [section] (e.g. `[mongodb] MONGO_URI = "..."`).
    """
    try:
        value = secrets.get(key, "")
        if value:
            return str(value)
    except Exception:
        pass
    if depth >= 3:
        return ""
    try:
        for sub in secrets.keys():
            try:
                value = secrets[sub]
            except Exception:
                continue
            if isinstance(value, Mapping):
                found = _find_secret(value, key, depth + 1)
                if found:
                    return found
    except Exception:
        pass
    return ""


def _configure():
    global _configured, _config_error, db
    if _configured:
        return
    _config_error = None
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(REPO_ROOT, ".env"))
    except Exception:
        pass
    try:
        secrets = st.secrets
        if secrets.load_if_toml_exists():
            for key in _SECRET_KEYS:
                value = _find_secret(secrets, key)
                if value:
                    os.environ.setdefault(key, value)
    except Exception as exc:
        _config_error = f"secrets.toml could not be parsed ({type(exc).__name__}): {exc}"
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


def _safe_host():
    """Hostname of the configured Mongo URI (credentials redacted)."""
    uri = os.environ.get("MONGO_URI") or ""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(uri.replace("mongodb+srv://", "http://").replace("mongodb://", "http://"))
        return parsed.hostname or ""
    except Exception:
        return ""


def health():
    return True


def diagnostics():
    """Fast, non-blocking config status (no network calls)."""
    _configure()
    return {
        "secrets_parse_error": _config_error,
        "mongo_uri_set": bool(os.environ.get("MONGO_URI")),
        "mongo_host": _safe_host(),
        "mongo_last_error": getattr(db, "last_error", None),
        "gemini_key_set": bool(os.environ.get("GEMINI_API_KEY")),
        "model_disabled": bool(os.environ.get("SCAMSHIELD_DISABLE_MODEL")),
        "model": _model_ref() or None,
    }


def ping_db():
    """Blocking MongoDB connection check (for the diagnostics panel)."""
    _configure()
    if not os.environ.get("MONGO_URI"):
        return False, "MONGO_URI is not set. Check the Secrets tab."
    last_error = "No attempt made"
    for _ in range(2):
        try:
            if db.is_connected():
                return True, "connected"
            last_error = getattr(db, "last_error", None) or "unknown error"
        except Exception as exc:
            last_error = str(exc)
    return False, last_error


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
    if db.insert_report(report):
        return {"status": "saved", "report": report}
    error = getattr(db, "last_error", None) or "connection failed"
    return {"status": "offline", "message": f"Reports DB not reachable: {error}"}


def recent_reports(limit=15):
    _configure()
    limit = max(1, min(int(limit), 50))
    return {"reports": db.recent_reports(limit)}
