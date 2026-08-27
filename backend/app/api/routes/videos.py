from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.source_video import SourceVideo
from app.schemas.video import SourceVideoCreate, SourceVideoOut

router = APIRouter(prefix="/videos", tags=["videos"])


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
