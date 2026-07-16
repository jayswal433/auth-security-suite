"""Command-line entry point for running brute-force without the API server.

Usage:
    python -m auth_security_suite.cli
    auth-security-suite          # after pip install -e .
"""

import logging

from auth_security_suite.core.settings import get_settings
from auth_security_suite.worker.brute_force_runner import BruteForceRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run brute-force from the command line using .env configuration.

    Reads ``AUTH_SECURITY_START_LENGTH``, ``AUTH_SECURITY_START_FROM``, and
    ``AUTH_SECURITY_HEADLESS`` from the environment / .env file, then blocks
    until the job finishes.
    """
    settings = get_settings()
    runner = BruteForceRunner(settings=settings)

    job_id = runner.start(
        start_length=settings.start_length,
        start_from=settings.start_from,
        headless=settings.headless,
    )
    logger.info("Started CLI job %s", job_id)

    # Block until the background thread completes
    if runner._thread:
        runner._thread.join()

    state = runner.get_state()
    if state.found_password:
        logger.info("Found password: %s", state.found_password)
    else:
        logger.info("Finished: %s", state.message)


if __name__ == "__main__":
    main()
