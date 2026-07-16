"""Auth Security Suite — FastAPI security testing application.

This package provides a Playwright-based brute-force runner exposed via:
- REST API (FastAPI)
- CLI entry point
- Docker + nginx deployment stack

Modules:
    core: Environment-backed configuration (pydantic-settings).
    services: Login testing and password combination generation.
    worker: Background job runner with thread-safe state.
    api: HTTP endpoints for starting, stopping, and monitoring jobs.
    schemas: Pydantic request/response models.
"""

__version__ = "0.1.0"
