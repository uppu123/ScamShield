import os
import time

from pymongo import MongoClient


class Database:
    def __init__(self, uri=None, dbname="scamshield"):
        self.client = None
        self.db = None
        self.last_error = None
        uri = uri or os.environ.get("MONGO_URI")
        if uri:
            try:
                self.client = MongoClient(uri, serverSelectionTimeoutMS=10000)
                self.db = self.client[dbname]
            except Exception as exc:
                self.last_error = f"init: {exc}"
                self.client = None
                self.db = None

    def is_connected(self):
        if self.client is None or self.db is None:
            return False
        try:
            self.client.admin.command("ping")
            self.last_error = None
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    @property
    def postings(self):
        return self.db.postings if self.db is not None else None

    @property
    def reports(self):
        return self.db.reports if self.db is not None else None

    @property
    def scam_patterns(self):
        return self.db.scam_patterns if self.db is not None else None

    def insert_posting(self, doc, retries=3, gap=1.5):
        return self._write_with_retry(self.postings, doc, retries, gap)

    def insert_report(self, doc, retries=3, gap=1.5):
        return self._write_with_retry(self.reports, doc, retries, gap)

    def _write_with_retry(self, collection, doc, retries=3, gap=1.5):
        """Insert a document, retrying on transient failures.

        The free Atlas M0 cluster idle-sleeps after ~60s of inactivity and takes
        a few seconds to wake; the first attempt wakes it and can time out, so we
        retry before giving up. Returns True on success.
        """
        if collection is None:
            self.last_error = "collection unavailable"
            return False
        for attempt in range(max(1, retries)):
            try:
                collection.insert_one(dict(doc))
                self.last_error = None
                return True
            except Exception as exc:
                self.last_error = str(exc)
                if attempt < retries - 1:
                    time.sleep(gap)
        return False

    def recent_reports(self, limit=20):
        if self.reports is None:
            return []
        for _ in range(3):
            try:
                cursor = self.reports.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
                return list(cursor)
            except Exception as exc:
                self.last_error = str(exc)
                time.sleep(1.5)
        return []


db = Database()
