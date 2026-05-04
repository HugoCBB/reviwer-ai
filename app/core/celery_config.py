from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "reviewer_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.api.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_routes={
        "app.api.tasks.review_pr": {"queue": "reviews"},
    },
    task_queues={
        "reviews": {"exchange": "reviews", "routing_key": "reviews"},
    },
)