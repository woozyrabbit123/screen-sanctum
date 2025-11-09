"""FastAPI server for ScreenSanctum API."""

from fastapi import FastAPI
from celery.result import AsyncResult

from screensanctum.workers.celery_app import celery_app
from screensanctum.workers.tasks import health_check_task
from screensanctum.api.models import JobStatus

# Create FastAPI app
app = FastAPI(
    title="ScreenSanctum API",
    description="Enterprise API Server for ScreenSanctum - Share your screen, not your secrets",
    version="3.0.0",
)


@app.get("/api/v1/health")
async def health():
    """Basic health check endpoint for the API server."""
    return {"status": "ok"}


@app.post("/api/v1/jobs/health-check")
async def create_health_check_job():
    """Create a health check job to test Celery worker connectivity."""
    task = health_check_task.apply_async()
    return {"job_id": task.id, "status": "pending"}


@app.get("/api/v1/jobs/health-check/{task_id}")
async def get_health_check_job(task_id: str):
    """Get the status and result of a health check job."""
    result = AsyncResult(task_id, app=celery_app)
    return {
        "job_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
