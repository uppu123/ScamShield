# Privacy & Security

- Postings and reports are stored **hashed** (`sha256`, first 16 hex chars) plus
  the raw text needed for analysis and the crowdsourced feed.
- No candidate PII is collected. Screenshots are used only for OCR.
- Never log full credentials; keep secrets in `.env` (gitignored).
- Consider automatic deletion of uploaded screenshots from S3 after OCR if you
  want stricter retention.
