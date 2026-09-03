from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.clip import Clip
from app.models.processing_job import ProcessingJob
from app.models.source_video import SourceVideo
from app.schemas.clip import ClipOut, ClipUpdate
from app.services.storage import to_playback_url

router = APIRouter(prefix="/clips", tags=["clips"])


def _to_clip_out(clip: Clip) -> ClipOut:
    out = ClipOut.model_validate(clip)
    out.playback_url = to_playback_url(clip.storage_url)
    return out


@router.get("/by-job/{job_id}", response_model=list[ClipOut])
def list_clips_for_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clips = (
        db.query(Clip)
        .join(ProcessingJob)
        .join(SourceVideo)
        .filter(ProcessingJob.id == job_id, SourceVideo.user_id == current_user.id)
        .order_by(Clip.highlight_score.desc())
        .all()
    )
    return [_to_clip_out(c) for c in clips]


@router.patch("/{clip_id}", response_model=ClipOut)
def update_clip(
    clip_id: str,
    payload: ClipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clip = (
        db.query(Clip)
        .join(ProcessingJob)
        .join(SourceVideo)
        .filter(Clip.id == clip_id, SourceVideo.user_id == current_user.id)
        .first()
    )
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(clip, field, value)

    db.commit()
    db.refresh(clip)
    return _to_clip_out(clip)
