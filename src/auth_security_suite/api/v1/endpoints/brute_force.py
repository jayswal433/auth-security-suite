"""REST API endpoints for brute-force job control.

Routes:
    POST /api/v1/brute-force/start  — launch a background job
    GET  /api/v1/brute-force/status — poll job progress
    POST /api/v1/brute-force/stop   — cancel a running job
"""

from fastapi import APIRouter, HTTPException, status

from auth_security_suite.api.deps import get_brute_force_runner
from auth_security_suite.schemas.brute_force import (
    BruteForceJobResponse,
    BruteForceStartRequest,
    BruteForceStatusResponse,
    JobStatus,
)

router = APIRouter(prefix="/brute-force", tags=["brute-force"])


@router.post("/start", response_model=BruteForceJobResponse)
def start_brute_force(payload: BruteForceStartRequest) -> BruteForceJobResponse:
    """Start a new brute-force job in the background.

    Only one job can run at a time. Pass ``start_from: null`` (or omit it)
    to begin from the first combination.
    """
    runner = get_brute_force_runner()
    try:
        job_id = runner.start(
            start_length=payload.start_length,
            start_from=payload.start_from,
            headless=payload.headless,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return BruteForceJobResponse(
        job_id=job_id,
        status=JobStatus.RUNNING,
        message="Brute-force job started",
    )


@router.get("/status", response_model=BruteForceStatusResponse)
def get_brute_force_status() -> BruteForceStatusResponse:
    """Return the current state of the brute-force job (running or last finished)."""
    state = get_brute_force_runner().get_state()
    return BruteForceStatusResponse(
        job_id=state.job_id,
        status=state.status,
        current_length=state.current_length,
        tried_count=state.tried_count,
        last_password=state.last_password,
        found_password=state.found_password,
        message=state.message,
        started_at=state.started_at,
        finished_at=state.finished_at,
    )


@router.post("/stop", response_model=BruteForceStatusResponse)
def stop_brute_force() -> BruteForceStatusResponse:
    """Request cancellation of the currently running brute-force job."""
    runner = get_brute_force_runner()
    state = runner.get_state()

    if state.status != JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No running brute-force job to stop",
        )

    runner.stop()
    return BruteForceStatusResponse(
        job_id=state.job_id,
        status=JobStatus.STOPPED,
        current_length=state.current_length,
        tried_count=state.tried_count,
        last_password=state.last_password,
        message="Stop requested",
        started_at=state.started_at,
    )
