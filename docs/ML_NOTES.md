# ML Notes

## Data
- **Dataset**: EMSCAD (Employment Scam Aegean Dataset) v1.
- **Source**: Kaggle `shivamb/emscad-employment-scam-classification-dataset`.
- **Location**: `data/raw/emscad.csv` (gitignored).
- Text built from `title + company_profile + description + requirements + benefits`.
- Label column: `fraudulent`.

## Training
- Model: `distilbert-base-uncased`, binary classification.
- Script: `python ml/train.py --data data/raw/emscad.csv --epochs 3 --batch-size 16`
- Tokenizer: max length 256, truncation + padding.
- Metrics tracked: accuracy + F1 (metric_for_best_model = f1).
- `--balance` downsamples the majority class to the minority (866 fraud) → 1732
  rows (1385 train / 347 val), 261 steps at batch 16.
- `train.py` now sets `id2label = {0: "legitimate", 1: "fraudulent"}` so future
  saves produce readable labels (the 2026-08-12 save predates this and uses
  `LABEL_0`/`LABEL_1`; `ml/model.py` handles both).

## Experiment log
| Date       | Model      | Epochs | LR     | Accuracy | F1   | Notes |
| ---------- | ---------- | ------ | ------ | -------- | ---- | ----- |
| 2026-08-12 | DistilBERT | 3      | 2e-5   | 0.9135   | 0.9157 | Balanced, 256 max len, CPU |

## Known limitations
- **Domain mismatch**: the EMSCAD-trained model scores nearly every real-world
  short posting ~0.95+ fraud (its legit ads are long with description/benefits
  sections). Verified: on EMSCAD val it is accurate (fraud ~0.9+, legit
  ~0.01-0.06), but a short modern legit post scored 0.977. The combined pipeline
  still lands legit posts under 0.5 (0.5*rule + 0.4*model + 0.1*dup) when rules
  are quiet, but legit posts with a few weak rule hits may cross into SCAM.
- **Uncalibrated**: consider temperature scaling / a real-world calibration set
  before trusting `model_confidence` as a probability.

## Gotchas
- EMSCAD is class-imbalanced; consider class weights / oversampling if F1 drops.
- The pipeline falls back to the rule engine + keyword classifier until a model
  is trained — tests must keep passing without ML deps installed.
