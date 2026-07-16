"""Pydantic schemas for brute-force API requests and responses."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle states for a brute-force background job."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class BruteForceStartRequest(BaseModel):
    """Request body for POST /api/v1/brute-force/start."""

    start_length: int | None = Field(
        default=None,
        ge=1,
        description="Password length to begin with. Falls back to .env default.",
    )
    start_from: str | None = Field(
        default=None,
        description="Resume from this password. Omit or null to start from the beginning.",
    )
    headless: bool | None = Field(
        default=None,
        description="Run browser headless. Falls back to .env default.",
    )


class BruteForceJobResponse(BaseModel):
    """Response returned immediately after a job is accepted."""

    job_id: str
    status: JobStatus
    message: str


class BruteForceStatusResponse(BaseModel):
    """Snapshot of the current or most recent brute-force job."""

    job_id: str | None = None
    status: JobStatus
    current_length: int | None = None
    tried_count: int = 0
    last_password: str | None = None
    found_password: str | None = None
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
