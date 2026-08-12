#!/bin/bash
#
# ScamShield one-shot server bootstrap (Ubuntu 22.04, DigitalOcean droplet).
# Installs Docker, clones the repo, fetches the trained model from HF Hub,
# and starts the full stack behind nginx (self-signed TLS for demo).
#
# Usage (on a fresh droplet):
#   export MONGO_URI='mongodb+srv://...'
#   export GEMINI_API_KEY='...'
#   curl -fsSL https://raw.githubusercontent.com/uppu123/ScamShield/main/deploy/server_bootstrap.sh | bash
#
# or download + run:  bash server_bootstrap.sh
set -euo pipefail

echo "==> Installing Docker"
apt-get update -y
apt-get install -y docker.io docker-compose-v2
systemctl enable --now docker

echo "==> Cloning repo"
git clone https://github.com/uppu123/ScamShield.git /opt/scam-shield
cd /opt/scam-shield

echo "==> Fetching trained model from HF Hub"
docker run --rm -v "$PWD":/work -w /work python:3.11-slim \
  sh -c "pip install -q huggingface_hub && python scripts/fetch_model.py"

echo "==> Writing .env (secrets from environment)"
cat > .env <<EOF
MONGO_URI=${MONGO_URI:-}
GEMINI_API_KEY=${GEMINI_API_KEY:-}
TESSERACT_CMD=tesseract
PORT=5000
BACKEND_URL=http://localhost:5000
EOF

echo "==> Opening firewall (22,80,443)"
ufw allow 22,80,443/tcp >/dev/null 2>&1 || true

echo "==> Building & starting stack (first build takes ~7 min)"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "==> Done"
echo "Dashboard:  https://$(curl -s ifconfig.me)   (self-signed cert - expect a browser warning)"
echo "Direct API: http://$(curl -s ifconfig.me):5000/health"
