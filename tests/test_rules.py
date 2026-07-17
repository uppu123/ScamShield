from backend.core.rules import RuleEngine

SCAM_TEXT = (
    "Urgent hiring! Work from home, no experience needed. Earn up to Rs 50,000 per month. "
    "Pay a one-time registration fee of Rs 2000 to book your seat. Limited seats, apply within 24 hours. "
    "Contact hr.department45@gmail.com"
)

CLEAN_TEXT = (
    "Software Engineer at Acme Corp. 4-6 years of experience required. "
    "Email careers@acme.com to apply. Salary Rs 12,00,000 per annum with benefits."
)


def test_scam_text_triggers_fee_rule():
    hits = RuleEngine().analyze(SCAM_TEXT)
    assert any(hit.rule_id == "fee_request" for hit in hits)


def test_scam_text_triggers_multiple_rules():
    hits = RuleEngine().analyze(SCAM_TEXT)
    assert len(hits) >= 4


def test_clean_text_triggers_no_rules():
    hits = RuleEngine().analyze(CLEAN_TEXT)
    assert hits == []


def test_empty_text_no_hits():
    assert RuleEngine().analyze("") == []
