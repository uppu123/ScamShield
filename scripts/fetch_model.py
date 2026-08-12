"""Download the trained DistilBERT model from Hugging Face Hub into artifacts/model.

Usage:
    python scripts/fetch_model.py

Skips download if artifacts/model/model.safetensors already exists.
"""
import os
import sys

REPO = os.environ.get("SCAMSHIELD_MODEL_REPO", "nimoAlpha/scamshield-distilbert")
TARGET = os.path.join("artifacts", "model")
MARKER = os.path.join(TARGET, "model.safetensors")


def main() -> None:
    if os.path.exists(MARKER):
        print(f"Model already present at {TARGET}; nothing to do.")
        return

    from huggingface_hub import snapshot_download

    print(f"Downloading {REPO} -> {TARGET} ...")
    snapshot_download(repo_id=REPO, local_dir=TARGET)
    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
