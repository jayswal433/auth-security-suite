"""FastAPI dependency injection helpers."""

from auth_security_suite.worker.brute_force_runner import get_brute_force_runner

__all__ = ["get_brute_force_runner"]
