import os

TEMPLATES_PATH = "data/scam_templates.txt"


def _load_templates(path=None):
    path = path or os.environ.get("SCAM_TEMPLATES", TEMPLATES_PATH)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


class TemplateMatcher:
    def __init__(self, templates=None, threshold=0.8):
        self.threshold = threshold
        self.model = None
        self.templates = templates if templates is not None else _load_templates()
        self.embeddings = None
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            if self.templates:
                self.embeddings = self.model.encode(self.templates, normalize_embeddings=True)
        except Exception:
            self.model = None

    def most_similar(self, text):
        if self.model is None or not self.templates:
            return None, 0.0
        import numpy as np

        embedding = self.model.encode([text], normalize_embeddings=True)[0]
        scores = self.embeddings @ embedding
        index = int(np.argmax(scores))
        return index, float(scores[index])

    def is_near_duplicate(self, text):
        index, score = self.most_similar(text)
        template = self.templates[index] if index is not None else None
        return score >= self.threshold, score, template
