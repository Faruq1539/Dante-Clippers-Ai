from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.source_video import SourceVideo
from app.models.processing_job import ProcessingJob
from app.schemas.job import ProcessingJobCreate, ProcessingJobOut
from app.services.credit_service import charge_for_processing
from app.worker.tasks import process_video_task

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=ProcessingJobOut)
def create_processing_job(
    payload: ProcessingJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = (
        db.query(SourceVideo)
        .filter(SourceVideo.id == payload.source_video_id, SourceVideo.user_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Source video not found")
    if not video.duration_seconds:
        raise HTTPException(status_code=400, detail="Video duration unknown -- cannot price this job yet")

    # Charge credits BEFORE enqueuing so we never do billable compute work
    # for a job we can't charge for.
    charge_for_processing(db, current_user, video.duration_seconds)

    job = ProcessingJob(source_video_id=video.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    process_video_task.delay(str(job.id))

    return job


@router.get("/{job_id}", response_model=ProcessingJobOut)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(ProcessingJob).join(SourceVideo).filter(
        ProcessingJob.id == job_id, SourceVideo.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
