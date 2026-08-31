"""
Object storage helpers. Uses S3 when AWS credentials are configured;
otherwise falls back to a local folder on disk, which is genuinely useful
for local development and testing without needing real cloud credentials.

Callers just deal with `storage_url` strings (s3://..., file://..., or a
plain https:// URL for input) and never need to know which backend is
actually in use.
"""

import os
import shutil
import tempfile
import uuid

from app.config import settings

_s3_client = None

LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "local_storage")


def _using_s3() -> bool:
    return bool(settings.aws_access_key_id and settings.aws_secret_access_key and settings.storage_bucket)


def _get_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client(
            "s3",
            region_name=settings.storage_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
    return _s3_client


def download_to_temp(storage_url: str, suffix: str = ".mp4") -> str:
    """Download/copy a source into a local temp file and return its path."""
    fd, local_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    if storage_url.startswith("s3://"):
        _, _, rest = storage_url.partition("s3://")
        bucket, _, key = rest.partition("/")
        _get_client().download_file(bucket, key, local_path)
    elif storage_url.startswith("file://"):
        source_path = storage_url[len("file://"):]
        shutil.copyfile(source_path, local_path)
    elif storage_url.startswith("http://") or storage_url.startswith("https://"):
        import requests
        with requests.get(storage_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    else:
        # Treat as a plain local filesystem path (e.g. C:\Users\...\video.mp4)
        shutil.copyfile(storage_url, local_path)

    return local_path


def upload_file(local_path: str, key_prefix: str = "clips") -> str:
    """Upload a local file and return its storage URL (s3:// or file://)."""
    ext = os.path.splitext(local_path)[1] or ".mp4"
    key = f"{key_prefix}/{uuid.uuid4()}{ext}"

    if _using_s3():
        _get_client().upload_file(local_path, settings.storage_bucket, key)
        return f"s3://{settings.storage_bucket}/{key}"

    dest_dir = os.path.join(LOCAL_STORAGE_DIR, key_prefix)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{uuid.uuid4()}{ext}")
    shutil.copyfile(local_path, dest_path)
    return f"file://{dest_path}"


def cleanup(*paths: str) -> None:
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass
