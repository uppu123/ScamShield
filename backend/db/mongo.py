import os

from pymongo import MongoClient


class Database:
    def __init__(self, uri=None, dbname="scamshield"):
        self.client = None
        self.db = None
        uri = uri or os.environ.get("MONGO_URI")
        if uri:
            try:
                self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
                self.db = self.client[dbname]
            except Exception:
                self.client = None
                self.db = None

    def is_connected(self):
        if self.client is None or self.db is None:
            return False
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    @property
    def postings(self):
        return self.db.postings if self.db else None

    @property
    def reports(self):
        return self.db.reports if self.db else None

    @property
    def scam_patterns(self):
        return self.db.scam_patterns if self.db else None

    def insert_posting(self, doc):
        if self.postings is not None:
            self.postings.insert_one(doc)

    def insert_report(self, doc):
        if self.reports is not None:
            self.reports.insert_one(doc)

    def recent_reports(self, limit=20):
        if self.reports is None:
            return []
        cursor = self.reports.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)


db = Database()
