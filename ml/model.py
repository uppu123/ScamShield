import math
import os
import re

FALLBACK_TERMS = {
    "registration fee": 3,
    "processing fee": 3,
    "security deposit": 3,
    "pay to apply": 3,
    "transfer money": 3,
    "send money": 3,
    "refundable deposit": 3,
    "activation fee": 3,
    "registration charges": 3,
    "guaranteed income": 3,
    "guaranteed salary": 3,
    "earn per day": 3,
    "earn per week": 3,
    "apply within": 2,
    "limited seats": 2,
    "limited positions": 2,
    "no experience": 2,
    "data entry": 1,
    "typing job": 1,
    "copy paste": 2,
    "online forms": 1,
    "work from home": 1,
    "whatsapp": 2,
    "gmail": 2,
    "commission": 2,
    "payout": 2,
    "bonus": 1,
    "guarantee": 2,
    "urgent": 1,
    "hurry": 1,
    "asap": 1,
    "last chance": 2,
    "payment": 1,
    "salary": 1,
    "income": 1,
    "earn": 2,
    "fresher": 1,
}


class ScamClassifier:
    def __init__(self, model_dir="artifacts/model"):
        self.model_dir = model_dir
        self.pipeline = None
        self._load()

    def _load(self):
        if not os.path.isdir(self.model_dir):
            return
        try:
            from transformers import pipeline

            self.pipeline = pipeline(
                "text-classification",
                model=self.model_dir,
                tokenizer=self.model_dir,
                top_k=None,
            )
        except Exception:
            self.pipeline = None

    def predict_proba(self, text):
        if self.pipeline is not None:
            try:
                result = self.pipeline(text)[0]
                for entry in result:
                    if "fraud" in entry.get("label", "").lower() or entry["label"] == "1":
                        return float(entry["score"])
            except Exception:
                pass
        return self._fallback(text)

    def _fallback(self, text):
        lowered = text.lower()
        score = sum(weight for term, weight in FALLBACK_TERMS.items() if term in lowered)
        return 1.0 / (1.0 + math.exp(-(score - 3.0)))
