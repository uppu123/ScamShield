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

## Experiment log
| Date       | Model      | Epochs | LR     | Accuracy | F1   | Notes |
| ---------- | ---------- | ------ | ------ | -------- | ---- | ----- |
| TBD        | DistilBERT | 3      | 2e-5   | TBD      | TBD  | First run |

## Gotchas
- EMSCAD is class-imbalanced; consider class weights / oversampling if F1 drops.
- The pipeline falls back to the rule engine + keyword classifier until a model
  is trained — tests must keep passing without ML deps installed.
