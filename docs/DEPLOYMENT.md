# Deployment (AWS EC2 + Docker)

## Prerequisites
- Docker installed on the EC2 instance (Ubuntu 22.04).
- MongoDB Atlas cluster; set `MONGO_URI` in `.env`.
- Tesseract is installed inside the image; no host install needed.

## Steps

```bash
# on the instance
git clone <repo-url> scam-shield && cd scam-shield
cp .env.example .env            # fill in MONGO_URI, AWS keys
docker compose up --build -d
```

- API on port 5000, dashboard on 8501.
- Put Nginx in front for TLS + reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name app.example.com;
    location / { proxy_pass http://127.0.0.1:8501; }
    location /api/ { proxy_pass http://127.0.0.1:5000/; }
}
```

## Production notes
- Run `docker compose` with restart policies and a healthcheck (already wired).
- Move MongoDB Atlas / S3 credentials to Secrets Manager or container secrets.
- Scale the API with more Gunicorn workers behind an ELB.
