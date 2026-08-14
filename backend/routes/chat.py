from flask import Blueprint, jsonify, request

from ..chat_service import _answer, _llm_reply

bp = Blueprint("chat", __name__)


@bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty_message"}), 400
    history = data.get("history") or []

    reply = _llm_reply(history, message)
    if reply:
        return jsonify({"message": message, "reply": reply, "source": "llm"})
    return jsonify({"message": message, "reply": _answer(message), "source": "faq"})
