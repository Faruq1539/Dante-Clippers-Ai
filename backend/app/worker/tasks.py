from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.processing_job import ProcessingJob
from app.models.clip import Clip
from app.models.brand_template import BrandTemplate
from app.worker import pipeline


@celery_app.task(name="process_video")
def process_video_task(job_id: str):
    """
    Main pipeline task, run by the Celery worker (see docker-compose.yml).
    Credits are charged at job-creation time in the API layer (see
    app/api/routes/jobs.py) -- this task just does the work.
    """
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return

        try:
            job.status = "transcribing"
            db.commit()
            segments = pipeline.transcribe(job.source_video.storage_url)
            job.transcript = " ".join(s.text for s in segments)

            job.status = "scoring"
            db.commit()
            candidates = pipeline.score_highlights(segments)
            selected = pipeline.select_segments(candidates)

            job.status = "rendering"
            db.commit()
            for candidate in selected:
                clip = Clip(
                    job_id=job.id,
                    start_ts=candidate.start,
                    end_ts=candidate.end,
                    highlight_score=candidate.score,
                    status="rendering",
                )
                db.add(clip)
                db.flush()

                brand_config = None
                if clip.brand_template_id:
                    template = db.query(BrandTemplate).filter(BrandTemplate.id == clip.brand_template_id).first()
                    if template:
                        brand_config = {
                            "font": template.font,
                            "primary_color": template.primary_color,
                            "accent_color": template.accent_color,
                            **(template.caption_style or {}),
                        }

                storage_url = pipeline.render_clip(
                    job.source_video.storage_url,
                    candidate.start,
                    candidate.end,
                    brand_template=brand_config,
                    transcript_segments=segments,
                )
                clip.storage_url = storage_url
                clip.status = "ready"

            job.status = "done"
            db.commit()

        except Exception as e:  # noqa: BLE001
            job.status = "failed"
            job.error_message = str(e)
            db.commit()

    finally:
        db.close()
