from celery import Celery

from app.config import settings

celery_app = Celery(
    "dante_clippers",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Ensure tasks are registered when the worker starts.
import app.worker.tasks  # noqa: E402,F401
