import pandas as pd
from sklearn.model_selection import train_test_split

TEXT_COLUMNS = ["title", "company_profile", "description", "requirements", "benefits"]
LABEL_COLUMN = "fraudulent"


def load_emscad(path="data/raw/emscad.csv"):
    df = pd.read_csv(path)
    if LABEL_COLUMN not in df.columns:
        raise ValueError(f"Missing label column '{LABEL_COLUMN}'. Not an EMSCAD CSV?")
    df = df.dropna(subset=[LABEL_COLUMN])
    df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(int)
    return df


def build_text(df, columns=None):
    cols = [c for c in (columns or TEXT_COLUMNS) if c in df.columns]
    if not cols:
        raise ValueError("No text columns found in the dataset")
    return df[cols].fillna("").agg(" ".join, axis=1)


def prepare(path="data/raw/emscad.csv", test_size=0.2, seed=42):
    df = load_emscad(path)
    df["text"] = build_text(df)
    train, val = train_test_split(
        df, test_size=test_size, stratify=df[LABEL_COLUMN], random_state=seed
    )
    return train.reset_index(drop=True), val.reset_index(drop=True)
