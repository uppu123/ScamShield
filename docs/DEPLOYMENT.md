# Deployment

Two supported paths:

1. **Streamlit Community Cloud (recommended, free)** — single-process app, no
   server to manage, no card required. See below.
2. **Docker / self-hosted** — the original 2-tier (Flask + Streamlit behind
   nginx). See the "Docker" section at the end.

## Option A — Streamlit Community Cloud (free)

Deploys directly from your GitHub repo. The dashboard runs the analysis
**in-process** (no separate Flask backend): `frontend/app.py` calls
`frontend/cloud_client.py`, which invokes the rule engine + ML model + chat
service + MongoDB directly.

### 1. Make the repo deployable

- Repo must be **public** (or you need a paid plan for private apps).
- `frontend/requirements.txt` is what the cloud installs (Streamlit looks in the
  entrypoint's directory first).
- `frontend/app.py` is the entrypoint.
- Secrets go in the dashboard (Settings → Secrets) — see step 4.

### 2. Deploy

1. Go to <https://share.streamlit.io> and sign in with GitHub.
2. **Create app** → select `uppu123/ScamShield` → branch `main` →
   entrypoint `frontend/app.py`.
3. In **Advanced settings** set **Python version 3.11 or 3.12** (torch 2.3.1
   has no wheels for 3.13/3.14 — Cloud defaults to 3.14, so the install fails
   with "error installing requirements" unless you pin it). To change the
   Python version of an existing app you must **delete and redeploy** it.
4. `frontend/requirements.txt` installs the **CPU-only** torch build
   (`torch==2.3.1+cpu` via `--extra-index-url https://download.pytorch.org/whl/cpu`)
   so the cloud build skips the ~2.5GB CUDA stack and finishes quickly.

### 3. Model

- If `artifacts/model` is missing (it's git-ignored), the app automatically
  pulls the trained model from Hugging Face: **`nimoAlpha/scamshield-distilbert`**
  (see `cloud_client._model_ref`).
- To disable the model entirely (low-memory environments), set the secret
  `SCAMSHIELD_DISABLE_MODEL = "1"` — the app then uses the rule engine + keyword
  heuristic only.

### 4. Secrets (Settings → Secrets)

```toml
MONGO_URI = "mongodb+srv://USER:PASS@cluster0.example.mongodb.net/scamshield"
GEMINI_API_KEY = "your-gemini-api-key"
SCAMSHIELD_MODEL = "nimoAlpha/scamshield-distilbert"
# SCAMSHIELD_DISABLE_MODEL = "1"
```

A committed template lives at `.streamlit/secrets.toml.example`. The real
`.streamlit/secrets.toml` is git-ignored.

### 5. Behaviour notes on the cloud

- **OCR**: the cloud runtime has no Tesseract binary, so screenshot analysis
  returns a graceful `ocr_unavailable` result instead of reading text. Text
  analysis, chat, reports, downloads and the model are unaffected.
- **Memory**: free public apps get ~1GB RAM. Loading torch + the 268MB model is
  tight but works; if the app is ever killed after "Analyze", set
  `SCAMSHIELD_DISABLE_MODEL = "1"` to fall back to the rule engine.
- **MongoDB Atlas**: the cluster is open to `0.0.0.0/0`, which is required for
  a serverless runtime. If you harden it, whitelist the cloud's egress IPs
  (they change) or keep it open — the DB contains only anonymized postings.

### Local run (unchanged)

```bash
python -m backend.app      # API on :5000 (optional for cloud_client)
streamlit run frontend/app.py   # dashboard on :8501
```

`frontend/cloud_client.py` reads secrets from the repo-root `.env` when running
locally, so both apps keep working even without the Flask backend.

## Option B — Docker (self-hosted)

Original 2-tier deployment (Flask API + Streamlit + nginx TLS) on any VM.

### Prerequisites
- Docker on the host (Ubuntu 22.04 recommended).
- MongoDB Atlas cluster; set `MONGO_URI` in `.env`.
- (Chat) Gemini API key; set `GEMINI_API_KEY` in `.env`.

### Quick start

```bash
git clone <repo-url> scam-shield && cd scam-shield
cp .env.example .env            # fill in MONGO_URI, GEMINI_API_KEY, AWS keys
docker compose up --build -d
```

- Dashboard: `https://<server-ip>` (port 80 redirects to 443, self-signed cert
  generated on first boot by `deploy/nginx-entrypoint.sh`).
- Direct API: port 5000.

> **Trained model**: `artifacts/model` (267MB) is **not tracked in git**. Ship
> it either by baking it into the image (build on a machine that has it) or by
> running `python scripts/fetch_model.py` on the host (downloads from HF Hub).

### TLS / reverse proxy (nginx)

Config lives in `deploy/nginx.conf`. `location /` → Streamlit (WebSocket
upgrades configured), `location /api/` → Flask backend, port 80 → 301 redirect.

For a production certificate, swap the self-signed certs for Let's Encrypt
(see the certificate example at the bottom of this file) and set `server_name`
in `deploy/nginx.conf`.

### MongoDB Atlas — restrict IP allowlist

The cluster is currently open to `0.0.0.0/0` (any IP). **Restrict it for
self-hosting:**

1. cloud.mongodb.com → your cluster → **Network Access**.
2. Delete the `0.0.0.0/0` entry.
3. Add an allowlist entry for **your deployment's egress IP** (`curl ifconfig.me`
   on the server).
4. If the IP is dynamic, add your ISP CIDR or use a NAT with a static egress IP.

Do NOT restrict it if the app runs on Streamlit Community Cloud (serverless
egress IPs change) — keep `0.0.0.0/0` there.

### Production notes (Docker path)

- Add `restart: unless-stopped` to services (`docker-compose.prod.yml` does this).
- `docker-compose.prod.yml` also sets `GUNICORN_WORKERS=1` (fits 4GB droplets).
- CPU-only torch (`--index-url https://download.pytorch.org/whl/cpu`) can shrink
  the image from ~10.5GB to ~4GB.
- Move Mongo / S3 credentials to Secrets Manager or Docker secrets.
