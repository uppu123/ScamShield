import pytest

from backend.core.ocr import OCREngine


def test_ocr_reports_availability():
    engine = OCREngine()
    if not engine.is_available():
        pytest.skip("Tesseract is not installed on this machine")
    assert engine.is_available() is True
