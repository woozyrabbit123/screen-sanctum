"""Celery application configuration."""

from celery import Celery

# Create Celery app instance
celery_app = Celery(
    "screensanctum",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Auto-discover tasks from the tasks module
celery_app.autodiscover_tasks(["screensanctum.workers"])

# Alias for Celery CLI compatibility
app = celery_app
