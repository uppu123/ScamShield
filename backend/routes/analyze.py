import hashlib
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from ..core.pipeline import ScamPipeline
from ..db.mongo import db

bp = Blueprint("analyze", __name__)
pipeline = ScamPipeline()


@bp.post("/analyze_text")
def analyze_text():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    result = pipeline.analyze_text(text)
    if result.get("error"):
        return jsonify(result), 400
    result["type"] = "text"
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    if db.is_connected():
        db.insert_posting(result)
    return jsonify(result)


@bp.post("/analyze_image")
def analyze_image():
    file = request.files.get("image")
    if file is None:
        return jsonify({"error": "missing_file", "message": "Attach an image."}), 400
    image_bytes = file.read()
    result = pipeline.analyze_image(image_bytes)
    if result.get("error"):
        return jsonify(result), 400
    result["type"] = "image"
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["hash"] = hashlib.sha256(image_bytes).hexdigest()[:16]
    if db.is_connected():
        db.insert_posting(result)
    return jsonify(result)
