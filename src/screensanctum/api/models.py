"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field


class RedactRequest(BaseModel):
    """Request model for redaction job submission."""

    image_b64: str = Field(..., max_length=20 * 1024 * 1024)
    template_id: str


class JobStatus(BaseModel):
    """Response model for job submission."""

    job_id: str
    status: str


class JobResult(BaseModel):
    """Response model for job result retrieval."""

    job_id: str
    status: str
    result: str | None = None
