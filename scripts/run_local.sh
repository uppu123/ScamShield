#!/usr/bin/env bash
set -euo pipefail
python -m backend.app &
BACKEND_PID=$!
trap "kill $BACKEND_PID" EXIT
sleep 2
streamlit run frontend/app.py
