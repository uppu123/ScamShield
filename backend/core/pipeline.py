import os

from .dedup import TemplateMatcher
from .explain import build_explanation, highlight_flags
from .ocr import OCRImageError, OCREngine
from .rules import RuleEngine


class ScamPipeline:
    def __init__(self, config=None):
        self.config = config or {}
        self.rules = RuleEngine()
        self.ocr = OCREngine()
        self.matcher = TemplateMatcher(
            threshold=self.config.get("dup_threshold", 0.8)
        )
        self.classifier = None
        try:
            from ml.model import ScamClassifier

            self.classifier = ScamClassifier(
                self.config.get("model_dir", "artifacts/model")
            )
        except Exception:
            self.classifier = None

    def analyze_text(self, text):
        text = (text or "").strip()
        if not text:
            return {"error": "empty_text", "message": "Provide a job posting to analyze."}
        hits = self.rules.analyze(text)
        rule_score = self.rules.score(hits)
        model_conf = None
        if self.classifier is not None:
            try:
                model_conf = self.classifier.predict_proba(text)
            except Exception:
                model_conf = None
        duplicate_score = None
        if self.matcher.model is not None:
            index, sim = self.matcher.most_similar(text)
            if sim >= self.matcher.threshold:
                duplicate_score = sim
        score = self._combine(rule_score, model_conf, duplicate_score)
        return {
            "score": score,
            "label": "SCAM" if score >= 0.5 else "LIKELY LEGIT",
            "rule_score": rule_score,
            "model_confidence": model_conf,
            "duplicate_template_score": duplicate_score,
            "red_flags": [hit.to_dict() for hit in hits],
            "explanation": build_explanation(hits, model_conf, duplicate_score),
            "highlighted_text": highlight_flags(text, hits),
        }

    def analyze_image(self, image_bytes):
        try:
            ocr_text, ok = self.ocr.extract_text(image_bytes)
        except OCRImageError as exc:
            return {"error": "invalid_image", "message": str(exc)}
        if not ok:
            return {
                "error": "ocr_unavailable",
                "message": "OCR engine unavailable. Install Tesseract and set TESSERACT_CMD.",
            }
        if not ocr_text:
            return {"error": "no_text", "message": "No text could be read from the image."}
        result = self.analyze_text(ocr_text)
        result["source"] = "image"
        result["ocr_text"] = ocr_text
        return result

    def _combine(self, rule_score, model_conf, duplicate_score):
        dup = duplicate_score if duplicate_score is not None else 0.0
        if model_conf is not None:
            return round(0.5 * rule_score + 0.4 * model_conf + 0.1 * dup, 4)
        return round(0.85 * rule_score + 0.15 * dup, 4)
