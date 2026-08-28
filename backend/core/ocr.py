"""Tesseract OCR wrapper with cross-platform binary discovery.

Tries, in order:
  1. TESSERACT_CMD / TESSERACT_PATH environment variable
  2. `tesseract` on PATH (Linux / macOS / Docker, or Windows with it on PATH)
  3. Common Windows install locations (Program Files, LOCALAPPDATA, user dirs)
  4. Common Unix locations (/usr/bin, /usr/local/bin, Homebrew)
"""

import glob
import io
import os
import shutil

from PIL import Image


class OCRImageError(Exception):
    """Raised when the uploaded bytes cannot be decoded as an image."""


def _home_tesseract_candidates():
    dirs = []
    for pattern in (
        r"C:\Users\*\AppData\Local\Tesseract-OCR\tesseract.exe",
        r"C:\Users\*\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ):
        dirs.extend(glob.glob(pattern))
    return dirs


def discover_tesseract():
    """Return a usable Tesseract binary path, or None."""
    explicit = (
        os.environ.get("TESSERACT_CMD")
        or os.environ.get("TESSERACT_PATH")
        or ""
    ).strip().strip('"')
    if explicit:
        return explicit
    found = shutil.which("tesseract")
    if found:
        return found
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local"), "Tesseract-OCR", "tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    for path in _home_tesseract_candidates():
        if os.path.isfile(path):
            return path
    return None


class OCREngine:
    def __init__(self, tesseract_cmd=None, lang="eng"):
        self.tesseract_cmd = tesseract_cmd or discover_tesseract()
        self.lang = lang
        self._available = None
        self._error = None

    def is_available(self):
        if self._available is None:
            try:
                import pytesseract

                if self.tesseract_cmd:
                    pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
                pytesseract.get_tesseract_version()
                self._available = True
                self._error = None
            except FileNotFoundError as exc:
                self._available = False
                self._error = str(exc) or "tesseract binary not found"
            except Exception as exc:
                self._available = False
                self._error = f"{type(exc).__name__}: {exc}"
        return self._available

    def error(self):
        """Human-readable reason OCR is unavailable (None when it works)."""
        self.is_available()
        return self._error

    def extract_text(self, image_bytes):
        if not self.is_available():
            return "", False
        import pytesseract

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except Exception:
            raise OCRImageError("The uploaded file could not be read as an image.") from None
        try:
            text = pytesseract.image_to_string(image, lang=self.lang)
        except Exception:
            return "", False
        return text.strip(), True