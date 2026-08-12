#!/bin/sh
set -e

gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 backend.app:app &
BACKEND_PID=$!

echo "Waiting for backend health check..."
for i in $(seq 1 60); do
  if curl -fsS http://localhost:5000/health >/dev/null 2>&1; then
    echo "Backend ready."
    break
  fi
  sleep 1
done

PORT=${PORT:-7860}
streamlit run frontend/app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true
STATUS=$?

kill "$BACKEND_PID" 2>/dev/null || true
exit "$STATUS"
