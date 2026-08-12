# Deployment (AWS EC2 + Docker)

## Prerequisites
- Docker installed on the EC2 instance (Ubuntu 22.04).
- MongoDB Atlas cluster; set `MONGO_URI` in `.env`.
- (Chat) Gemini API key; set `GEMINI_API_KEY` in `.env`.
- Tesseract is installed inside the image; no host install needed.

## Quick start

```bash
# on the instance
git clone <repo-url> scam-shield && cd scam-shield
cp .env.example .env            # fill in MONGO_URI, GEMINI_API_KEY, AWS keys
docker compose up --build -d
```

> **Trained model**: `artifacts/model` (267MB) is **not tracked in git** (see
> `.gitignore`), so a fresh clone has no model and the API silently falls back
> to the rule engine. To ship the model (baked into the image), build the image
> on a machine that has `artifacts/model` and use the registry flow below.
>
> ```bash
> # on a machine WITH the model (e.g. dev)
> docker build -t <registry>/scam-shield:latest .
> docker push <registry>/scam-shield:latest
>
> # docker-compose.yml backend service: replace `build: .` with `image: <registry>/scam-shield:latest`
> # on the server
> docker compose pull && docker compose up -d
> ```
>
> Alternative: `scp -r artifacts <server>:~/scam-shield/` before
> `docker compose up --build -d`.

- Dashboard: `https://<server-ip>` (port 80 redirects to 443).
- Direct API (bypass proxy): port 5000.
- An `nginx` service terminates TLS in front of Streamlit. On first boot it
  generates a **self-signed** certificate (`deploy/nginx-entrypoint.sh`, stored
  in the `nginx-certs` volume). For production, replace it with a Let's Encrypt
  cert (see below) and set `server_name` in `deploy/nginx.conf`.

## TLS / reverse proxy (nginx)

Config lives in `deploy/nginx.conf`; a service in `docker-compose.yml` runs it.

- `location /` → Streamlit (WebSocket upgrades are configured).
- `location /api/` → Flask backend (proxies `/api/...` to `:5000/...`).
- Port 80 → 301 redirect to HTTPS.

### Production certificate (Let's Encrypt, recommended)

```bash
docker compose exec nginx sh -c "ls /etc/nginx/certs"   # after first boot
# Then swap the self-signed certs for a real one, e.g. with certbot on the host:
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d app.example.com -d www.app.example.com
# Copy the issued certs into the nginx volume:
docker cp /etc/letsencrypt/live/app.example.com/fullchain.pem <nginx-container>:/etc/nginx/certs/fullchain.pem
docker cp /etc/letsencrypt/live/app.example.com/privkey.pem  <nginx-container>:/etc/nginx/certs/privkey.pem
docker compose restart nginx
```

Set `server_name app.example.com;` in `deploy/nginx.conf` and add a DNS A
record pointing `app.example.com` at the instance IP. Add a cron/certbot
renewal hook to keep the cert fresh (self-signed certs are valid 365 days).

## MongoDB Atlas — restrict IP allowlist

The cluster is currently open to `0.0.0.0/0` (any IP). **Restrict it now:**

1. Log in to [cloud.mongodb.com](https://cloud.mongodb.com) → your cluster
   (`cluster0`) → **Network Access**.
2. Delete the `0.0.0.0/0` entry.
3. Add an allowlist entry for **your deployment's egress IP**:
   - EC2: the instance's public/elastic IP (get it from
     `curl ifconfig.me` run on the instance), or the NAT gateway IP.
   - Home: your public IP.
4. If the IP is dynamic, add the CIDR for your ISP range or use a VPC/NAT with
   a static egress IP.

This is a manual dashboard step (requires your Atlas account) — the IP can be
fetched with `curl ifconfig.me` on the server before adding it.

## Production notes
- `docker compose` has restart policies via the healthcheck; add
  `restart: unless-stopped` to services if desired.
- Move MongoDB Atlas / S3 credentials to Secrets Manager or Docker secrets.
- Scale the API with more Gunicorn workers behind an ELB.
- The Streamlit service `pip install`s its deps at container start — build a
  dedicated frontend image for faster cold starts.
