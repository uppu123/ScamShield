import os

from dotenv import load_dotenv

from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .routes.analyze import bp as analyze_bp
from .routes.chat import bp as chat_bp
from .routes.report import bp as report_bp


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(chat_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
