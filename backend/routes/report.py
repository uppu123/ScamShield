import hashlib
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..db.mongo import db

bp = Blueprint("report", __name__)


@bp.post("/report_scam")
def report_scam():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty_text", "message": "Provide the scam posting text."}), 400
    report = {
        "text": text,
        "notes": data.get("notes", ""),
        "source": data.get("source", "unknown"),
        "contact": data.get("contact", ""),
        "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if db.is_connected():
        db.insert_report(report)
        return jsonify({"status": "saved", "report": report})
    return jsonify({"status": "offline", "message": "Reports DB not configured; nothing stored."}), 503


@bp.get("/reports")
def recent_reports():
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, 50))
    return jsonify({"reports": db.recent_reports(limit)})
