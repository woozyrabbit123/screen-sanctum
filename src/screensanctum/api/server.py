"""FastAPI server for ScreenSanctum API."""

from fastapi import FastAPI, Depends
from celery.result import AsyncResult

from screensanctum.workers.celery_app import celery_app
from screensanctum.workers.tasks import redact_image_task
from screensanctum.api.models import RedactRequest, JobStatus, JobResult
from screensanctum.api.security import get_api_key

# Create FastAPI app
app = FastAPI(
    title="ScreenSanctum API",
    description="Enterprise API Server for ScreenSanctum - Share your screen, not your secrets",
    version="3.0.0",
)


@app.post("/api/v1/jobs/redact", response_model=JobStatus)
def submit_redaction_job(
    request: RedactRequest,
    api_key: str = Depends(get_api_key)
):
    """Submit a redaction job for asynchronous processing.

    Args:
        request: RedactRequest containing base64-encoded image and template_id.
        api_key: API key for authentication (from X-API-Key header).

    Returns:
        JobStatus with job_id and initial status.
    """
    task = redact_image_task.apply_async(
        args=[request.image_b64, request.template_id]
    )
    return {"job_id": task.id, "status": "pending"}


@app.get("/api/v1/jobs/{job_id}", response_model=JobResult)
def get_job_result(
    job_id: str,
    api_key: str = Depends(get_api_key)
):
    """Get the status and result of a redaction job.

    Args:
        job_id: The ID of the job to retrieve.
        api_key: API key for authentication (from X-API-Key header).

    Returns:
        JobResult with job_id, status, and result (if completed).
    """
    task_result = AsyncResult(job_id, app=celery_app)
    return {
        "job_id": job_id,
        "status": task_result.status,
        "result": task_result.result if task_result.successful() else None
    }
