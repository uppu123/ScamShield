import io
import os

from PIL import Image


class OCREngine:
    def __init__(self, tesseract_cmd=None, lang="eng"):
        self.tesseract_cmd = tesseract_cmd or os.environ.get("TESSERACT_CMD")
        self.lang = lang
        self._available = None

    def is_available(self):
        if self._available is None:
            try:
                import pytesseract

                if self.tesseract_cmd:
                    pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
                pytesseract.get_tesseract_version()
                self._available = True
            except Exception:
                self._available = False
        return self._available

    def extract_text(self, image_bytes):
        if not self.is_available():
            return "", False
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang=self.lang)
        return text.strip(), True
