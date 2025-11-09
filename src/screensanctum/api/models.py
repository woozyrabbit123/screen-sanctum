"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel


class JobStatus(BaseModel):
    """Response model for job status."""

    job_id: str
    status: str
    result: str | None = None
