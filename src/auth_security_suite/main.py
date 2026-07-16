"""FastAPI application entry point.

Creates the app, registers routes, and exposes ``app`` for uvicorn / Docker.
"""

import logging

from fastapi import FastAPI

from auth_security_suite.api.v1.router import api_router
from auth_security_suite.core.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance.

    Registers:
        - GET /health          — liveness probe
        - /api/v1/brute-force  — job control endpoints
        - /docs, /redoc        — auto-generated API docs
    """
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe used by Docker healthcheck and nginx."""
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
