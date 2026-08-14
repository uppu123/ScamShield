from backend.db.mongo import Database


class _FlakyCollection:
    def __init__(self, failures):
        self.calls = 0
        self.failures = failures
        self.inserted = None

    def insert_one(self, doc):
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectionError("simulated wake-up timeout")
        self.inserted = doc


class _FakeDb:
    def __init__(self, failures):
        self.reports = _FlakyCollection(failures)
        self.postings = _FlakyCollection(failures)


def _make_db(failures=2):
    db = Database.__new__(Database)
    db.client = object()
    db.db = _FakeDb(failures)
    db.last_error = None
    return db


def test_insert_report_retries_on_transient_failure():
    db = _make_db(failures=2)
    ok = db.insert_report({"text": "scam posting"}, retries=3, gap=0)
    assert ok is True
    assert db.db.reports.inserted is not None
    assert db.last_error is None


def test_insert_report_returns_false_after_exhausting_retries():
    db = _make_db(failures=5)
    ok = db.insert_report({"text": "scam posting"}, retries=3, gap=0)
    assert ok is False
    assert db.db.reports.inserted is None
    assert db.last_error


def test_insert_report_fails_when_db_unavailable(monkeypatch):
    monkeypatch.delenv("MONGO_URI", raising=False)
    db = Database.__new__(Database)
    db.dbname = "scamshield"
    db.client = None
    db.db = None
    db.last_error = None
    ok = db.insert_report({"text": "x"}, retries=2, gap=0)
    assert ok is False
    assert "MONGO_URI" in db.last_error


def test_connect_repairs_stale_instance_when_uri_appears(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    db = Database.__new__(Database)
    db.dbname = "scamshield"
    db.client = None
    db.db = None
    db.last_error = None
    assert db.connect() is True
    assert db.client is not None
    assert db.db is not None
