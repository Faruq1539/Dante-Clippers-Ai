import subprocess
import tempfile
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.source_video import SourceVideo
from app.schemas.video import SourceVideoCreate, SourceVideoOut
from app.services import storage

router = APIRouter(prefix="/videos", tags=["videos"])


def _probe_duration_seconds(local_path: str) -> int | None:
    """Use ffprobe to get a video's duration. Returns None if it can't be read."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                local_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return int(float(result.stdout.strip()))
    except Exception:
        return None


@router.post("/upload", response_model=SourceVideoOut)
async def upload_source_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Real file upload endpoint -- this is what the mobile app calls when a
    user picks or records a video. The file is streamed in, saved to
    storage (S3 or local disk, whichever is configured), probed for its
    duration with ffprobe, and registered as a SourceVideo.

    This is the only upload path that should exist -- never accept an
    arbitrary external link and download it server-side (see
    docs/tech-spec.md section 5 for why).
    """
    suffix = os.path.splitext(file.filename or "")[1] or ".mp4"

    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        with open(temp_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        duration = _probe_duration_seconds(temp_path)
        storage_url = storage.upload_file(temp_path, key_prefix="uploads")
    finally:
        storage.cleanup(temp_path)

    video = SourceVideo(
        user_id=current_user.id,
        origin="upload",
        storage_url=storage_url,
        duration_seconds=duration,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.post("", response_model=SourceVideoOut)
def register_source_video(
    payload: SourceVideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Register a source video after it's been uploaded to object storage
    (client should request a presigned upload URL first, upload directly
    to storage, then call this endpoint with the resulting storage_url).

    `origin` must be "upload" or one of the OFFICIAL-API-backed platforms
    (tiktok, instagram, twitch, x) per docs/tech-spec.md section 5.
    Never accept an arbitrary link here and scrape it server-side.
    """
    video = SourceVideo(
        user_id=current_user.id,
        origin=payload.origin,
        storage_url=payload.storage_url,
        duration_seconds=payload.duration_seconds,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.get("", response_model=list[SourceVideoOut])
def list_source_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(SourceVideo).filter(SourceVideo.user_id == current_user.id).all()
