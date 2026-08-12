---
title: Scam Shield
emoji: 🛡️
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
license: apache-2.0
app_port: 7860
---

# Scam Shield

Fake job posting & recruitment fraud detector for the Indian job market.

Analyze a job posting (text or screenshot) and get a scam likelihood score with
explainable red flags, built on a fine-tuned DistilBERT model + rule engine.

## Single-container layout

- Flask backend on internal port `5000` (gunicorn)
- Streamlit frontend on `7860` (Hugging Face proxy port)
- Fine-tuned DistilBERT model baked in from `uppu123/scamshield-distilbert`

## Secrets

Set in Space settings:

- `MONGO_URI` — MongoDB Atlas connection string (reports feed)
- `GEMINI_API_KEY` — powers the "Ask ScamShield" chat
