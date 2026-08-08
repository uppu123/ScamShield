from backend.routes.chat import _answer


def test_fee_question():
    reply = _answer("Is asking for a registration fee normal?")
    assert "fee" in reply.lower()


def test_security_deposit_question():
    reply = _answer("Is a security deposit normal?")
    assert "deposit" in reply.lower()


def test_default_answer():
    reply = _answer("hello there")
    assert "paste the text" in reply.lower()
