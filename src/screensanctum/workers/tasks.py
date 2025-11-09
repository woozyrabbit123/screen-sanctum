"""Celery tasks for asynchronous processing."""

from screensanctum.workers.celery_app import celery_app


@celery_app.task
def health_check_task():
    """Simple health check task to verify Celery is working."""
    return "Celery worker is alive and well."
