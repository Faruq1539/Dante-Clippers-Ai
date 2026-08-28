"""
Object storage helpers (S3-compatible). Used by the worker pipeline to pull
source videos down for processing and push rendered clips back up.

Swap the boto3 calls here if you use GCS or another provider -- callers
just deal with `storage_url` strings and never touch boto3 directly.
"""

import os
import tempfile
import uuid

import boto3

from app.config import settings

_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.storage_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
    return _s3_client


def download_to_temp(storage_url: str, suffix: str = ".mp4") -> str:
    """
    Download an object to a local temp file and return its path.

    Accepts either an s3://bucket/key URL or a plain https:// URL (for
    cases where storage_url is already a signed/public link).
    """
    fd, local_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    if storage_url.startswith("s3://"):
        _, _, rest = storage_url.partition("s3://")
        bucket, _, key = rest.partition("/")
        _get_client().download_file(bucket, key, local_path)
    else:
        import requests

        with requests.get(storage_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    return local_path


def upload_file(local_path: str, key_prefix: str = "clips") -> str:
    """Upload a local file to the configured bucket and return its s3:// URL."""
    ext = os.path.splitext(local_path)[1] or ".mp4"
    key = f"{key_prefix}/{uuid.uuid4()}{ext}"
    _get_client().upload_file(local_path, settings.storage_bucket, key)
    return f"s3://{settings.storage_bucket}/{key}"


def cleanup(*paths: str) -> None:
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass
