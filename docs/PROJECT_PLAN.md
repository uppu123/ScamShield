# Project Plan

Goal: analyze a job posting (text or screenshot) and flag scam likelihood with
explainable red flags, built for the Indian job market.

## Day-by-day plan (5 hrs/day)

1. **Day 1 — Setup**: MongoDB Atlas schema (postings, scam_patterns, reports),
   EMSCAD dataset, S3 bucket, Tesseract OCR pipeline test.
2. **Day 2 — Model**: fine-tune DistilBERT on EMSCAD, evaluate accuracy.
3. **Day 3 — Rules**: regex/NER red-flag engine (fee mentions, generic contacts,
   salary anomalies, urgency); near-duplicate template detection via embeddings.
4. **Day 4 — Explainability**: combine model + rules into final score, build
   explanation generator.
5. **Day 5 — API**: Flask endpoints `/analyze_text`, `/analyze_image`,
   `/report_scam`, `/chat` wired to MongoDB Atlas.
6. **Day 6 — Frontend**: Streamlit dashboard — upload, score gauge, highlighted
   flags, chat widget, recent reports feed.
7. **Day 7 — Deploy**: Dockerize, deploy to AWS EC2, test on real anonymized
   scam postings, README + architecture diagram, demo video, resume bullets.

Compressed to a single intensive build day for this repository.
