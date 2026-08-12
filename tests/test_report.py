import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frontend"))

try:
    from report import build_pdf_report, _find_font_dir, _font_files

    _find_font_dir()
    _font_files()
    _REPORT_AVAILABLE = True
except Exception:
    _REPORT_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _REPORT_AVAILABLE,
    reason="No TrueType font available for PDF report",
)

SAMPLE_RESULT = {
    "score": 0.81,
    "label": "SCAM",
    "rule_score": 0.9,
    "model_confidence": None,
    "duplicate_template_score": 0.4,
    "type": "text",
    "red_flags": [
        {
            "name": "Fee request",
            "severity": 0.95,
            "explanation": "Asks for money to apply.",
            "evidence": ["Rs. 2,000"],
        }
    ],
    "explanation": {"bullet_points": ["Asks for a security deposit.", "Too-good salary for freshers."]},
}


def test_build_pdf_report_returns_pdf():
    data = build_pdf_report(SAMPLE_RESULT, "Pay Rs 2000 security deposit.")
    assert data[:4] == b"%PDF"
    assert len(data) > 1000


def test_build_pdf_report_handles_missing_optional_fields():
    minimal = {"score": 0.2, "label": "LIKELY LEGIT", "explanation": {"bullet_points": []}}
    data = build_pdf_report(minimal, "")
    assert data[:4] == b"%PDF"
