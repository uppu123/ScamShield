# EMSCAD — Employment Scam Aegean Dataset

The core labeled dataset for the scam classifier.

- Source: Kaggle — `shivamb/emscad-employment-scam-classification-dataset`
- Place the CSV at `data/raw/emscad.csv` (run `python scripts/download_emscad.py`)
- `data/raw/` is gitignored (large / third-party)

Key columns used: `title`, `description`, `requirements`, `benefits`,
`company_profile`, `fraudulent` (label).

`data/scam_templates.txt` holds real-world anonymized scam template texts used
for near-duplicate detection.
