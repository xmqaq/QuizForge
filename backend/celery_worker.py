from celery import Celery

from app.config import settings

celery = Celery(
    "quizforge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.ai_tasks"],
)

celery.conf.update(task_track_started=True, timezone="UTC")
