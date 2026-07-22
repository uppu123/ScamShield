from backend.core.pipeline import ScamPipeline

SCAM_TEXT = (
    "Urgent work from home, no experience, earn Rs 50,000 per month. "
    "Pay a registration fee of Rs 1000 to apply. Contact whatsapp."
)


def test_analyze_text_returns_full_result():
    pipe = ScamPipeline()
    result = pipe.analyze_text(SCAM_TEXT)
    assert result["score"] >= 0.5
    assert result["label"] == "SCAM"
    assert result["red_flags"]
    assert "highlighted_text" in result
    assert "explanation" in result


def test_analyze_empty_text_returns_error():
    result = ScamPipeline().analyze_text("   ")
    assert result["error"] == "empty_text"
