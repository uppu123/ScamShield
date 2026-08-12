FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      fonts-dejavu-core \
      git \
      curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone --depth 1 https://github.com/uppu123/ScamShield.git /app

RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt -r frontend/requirements.txt

ARG MODEL_REPO=uppu123/scamshield-distilbert
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='$MODEL_REPO', local_dir='artifacts/model')"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 7860
CMD ["/entrypoint.sh"]
