# ScamShield — Project Instructions

Fake job posting & recruitment fraud detector. Global rules from
`~/.config/opencode/AGENTS.md` apply.

## Project memory
- Lives in the Obsidian vault at `C:\scamshield\Projects\Scam Shield\` — start
  with `Memory.md`.
- Read it at the start of every session; update it as work progresses and at
  session end.
- Keep it current: goals, decisions, experiment results, TODOs, gotchas.

## Stack
- Backend: Flask (`backend/`), frontend: Streamlit (`frontend/`), ML: `ml/`
- DB: MongoDB Atlas (`MONGO_URI` in `.env`), OCR: Tesseract
- Deploy: Docker + Gunicorn

## Commands
- `python -m backend.app` — start API on :5000
- `streamlit run frontend/app.py` — start dashboard on :8501
- `python ml/train.py --data data/raw/emscad.csv` — fine-tune DistilBERT
- `pytest -q` — run tests

## ML practice notes
- Track EMSCAD data source/version, training seed, hyperparameters, and eval
  metrics (accuracy + F1) in the project memory.
- The pipeline must keep working without a trained model (rule engine fallback).
