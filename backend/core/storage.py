import io
import os

STORAGE_ENABLED = "AWS_ACCESS_KEY_ID" in os.environ and "S3_BUCKET" in os.environ


def upload_screenshot(image_bytes, key):
    if not STORAGE_ENABLED:
        return None
    try:
        import boto3

        session = boto3.Session(
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ.get("AWS_REGION", "ap-south-1"),
        )
        client = session.client("s3")
        client.upload_fileobj(io.BytesIO(image_bytes), os.environ["S3_BUCKET"], key)
        return f"s3://{os.environ['S3_BUCKET']}/{key}"
    except Exception:
        return None
