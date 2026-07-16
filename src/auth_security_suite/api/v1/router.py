"""Version 1 API router — aggregates all v1 endpoint modules."""

from fastapi import APIRouter

from auth_security_suite.api.v1.endpoints import brute_force

api_router = APIRouter()
api_router.include_router(brute_force.router)
