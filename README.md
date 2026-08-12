# ScamShield — Fake Job Posting & Recruitment Fraud Detector

ScamShield analyzes a job posting (paste the text or upload a screenshot) and
flags scam likelihood with **explainable red flags** — not just a score, but
*why* it looks suspicious. Built for the Indian job market where
WhatsApp/Telegram/LinkedIn scams ("work from home, Rs 50,000/month, pay a
registration fee") target freshers and job seekers.

## Why this is niche

- Uses the real labeled **EMSCAD** dataset (Employment Scam Aegean Dataset) — an
  actual dataset almost nobody ships an end-to-end product around.
- Adds an **India-specific scam-pattern layer**: upfront fees, too-good
  salaries, Gmail/personal-WhatsApp contacts instead of company domains,
  urgency pressure.
- **Screenshot OCR** support (WhatsApp forwards, LinkedIn post images).
- **Explainable**: highlighted red flags in the text + natural-language
  explanation + a Q&A chatbot.
- **Shareable reports**: download every analysis as JSON or a clean user-friendly
  PDF report.
- **Light / dark theme** toggle in the sidebar.
- **Crowdsourced feedback loop**: user-reported scams grow the pattern database.

## Architecture

```
                    ┌────────────────────────────────────────┐
 Screenshot ───────►│  OCR (Tesseract)                       │
                    │        │                               │
 Text ─────────────►│        ▼                               │
                    │  Red-flag rule engine (regex/NER)      │
                    │  DistilBERT scam classifier (EMSCAD)   │
                    │  Near-duplicate template detection      │
                    │        │                               │
                    │        ▼                               │
                    │  Explainable scoring + explanation     │──► Streamlit dashboard
                    │  Flask REST API                        │──► Chat (rule-based FAQ)
                    └────────────────────────────────────────┘
                              │
                              ▼
              MongoDB Atlas (postings, reports, scam_patterns)
```

### Tech stack
- **OCR**: Tesseract via `pytesseract`
- **NLP/DL**: fine-tuned DistilBERT on EMSCAD, spaCy-ready, sentence-transformers
  for near-duplicate template detection
- **Rules**: regex-based red-flag engine combined with model confidence
- **Backend**: Flask REST API
- **Frontend**: Streamlit
- **Storage**: MongoDB Atlas; screenshots to AWS S3 (optional)
- **Deployment**: Docker + Nginx/Gunicorn on AWS EC2

## Project layout

```
backend/       Flask API (app, routes, core pipeline, db)
ml/            data prep, DistilBERT training, inference wrapper
frontend/      Streamlit dashboard
config/        config.yaml
scripts/       download_emscad.py
tests/         pytest suite
data/          EMSCAD notes + scam template library
artifacts/     trained models (gitignored)
```

## Quickstart (local)

Prerequisites: Python 3.11, [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
installed and on PATH.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python scripts/download_emscad.py      # optional: fetch EMSCAD
python ml/train.py                     # optional: fine-tune DistilBERT (GPU recommended)

python -m backend.app                  # start API on :5000
streamlit run frontend/app.py          # start dashboard on :8501
```

The app is fully functional **without** a trained model — the pipeline falls
back to the rule engine + keyword classifier until you fine-tune DistilBERT.

## API

| Method | Endpoint          | Body                                    | Description                 |
| ------ | ----------------- | --------------------------------------- | --------------------------- |
| POST   | `/analyze_text`   | `{"text": "..."}`                       | Analyze a posting's text    |
| POST   | `/analyze_image`  | multipart `image`                       | OCR + analyze a screenshot  |
| POST   | `/report_scam`    | `{"text", "notes", "source"}`           | Crowdsource a scam report   |
| GET    | `/reports`        | `?limit=10`                             | Recent user-reported scams  |
| POST   | `/chat`           | `{"message": "..."}`                    | Q&A about a posting         |
| GET    | `/health`         | —                                       | Liveness check              |

Example response:

```json
{
  "score": 0.87,
  "label": "SCAM",
  "rule_score": 0.5,
  "model_confidence": null,
  "duplicate_template_score": null,
  "red_flags": [
    {"rule_id": "fee_request", "name": "Upfront fee requested",
     "severity": 1.0, "explanation": "The posting asks you to pay a fee...", "evidence": ["registration fee"]}
  ],
  "explanation": {"summary": "...", "bullet_points": ["..."]},
  "highlighted_text": "<mark>...</mark>"
}
```

## Docker

```bash
cp .env.example .env      # fill in MONGO_URI, GEMINI_API_KEY
docker compose up --build
# Dashboard  -> https://localhost  (nginx, TLS)  — self-signed cert on first boot
# Streamlit  -> http://localhost:8501
# API        -> http://localhost:5000
```

See `docs/DEPLOYMENT.md` for the Let's Encrypt/TLS swap and MongoDB Atlas IP
allowlist hardening.

## Fine-tuning the classifier

```bash
python ml/train.py --data data/raw/emscad.csv --epochs 3 --batch-size 16
```

Trained model + tokenizer are saved to `artifacts/model/` and auto-loaded by the
API on the next request.

## Tests

```bash
pytest -q
```

## Demo

```bash
python scripts/download_emscad.py   # optional
python -m backend.app               # API on :5000
streamlit run frontend/app.py       # dashboard on :8501
```

Paste a suspicious posting (or upload a screenshot), get the scam score gauge,
highlighted red flags, a plain-language explanation, and ask the chat "is asking
for a security deposit normal?". Example used for testing:

> Urgent hiring! Work from home, no experience needed. Earn up to Rs 50,000 per
> month. Pay a one-time registration fee of Rs 2000 to book your seat. Limited
> seats, apply within 24 hours. Contact hr.department45@gmail.com

## Roadmap / build plan (compressed to 1 day)

| Track           | Built in this repo                                          |
| --------------- | ----------------------------------------------------------- |
| OCR             | `backend/core/ocr.py`                                       |
| Classifier      | `ml/` (train + inference; fallback until trained)           |
| Red-flag rules  | `backend/core/rules.py`                                     |
| Dedup           | `backend/core/dedup.py`                                     |
| Explainability  | `backend/core/explain.py`                                   |
| API             | `backend/` (`/analyze_text`, `/analyze_image`, `/report_scam`, `/chat`) |
| Frontend        | `frontend/app.py`                                           |
| Storage         | `backend/db/mongo.py` (MongoDB Atlas)                       |
| Deploy          | `Dockerfile`, `docker-compose.yml`                          |

## Next steps
- Fine-tune DistilBERT on the full EMSCAD dataset and record eval metrics.
- Add spaCy NER for company/entity extraction.
- Upload screenshots to AWS S3.
- Deploy to AWS EC2 behind Nginx/Gunicorn and test on real anonymized postings.
