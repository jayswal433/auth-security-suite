"""Background brute-force job runner.

Runs password guessing in a daemon thread so the FastAPI server stays responsive.
A single global runner instance is shared across API requests.
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from playwright.sync_api import sync_playwright

from auth_security_suite.core.settings import Settings, get_settings
from auth_security_suite.schemas.brute_force import JobStatus
from auth_security_suite.services.login_tester import LoginTester
from auth_security_suite.services.password_generator import tiered_combinations

logger = logging.getLogger(__name__)


@dataclass
class BruteForceState:
    """Thread-safe snapshot of a running or finished brute-force job."""

    job_id: str | None = None
    status: JobStatus = JobStatus.IDLE
    current_length: int | None = None
    tried_count: int = 0
    last_password: str | None = None
    found_password: str | None = None
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class BruteForceRunner:
    """Manages the lifecycle of a brute-force job in a background thread.

    Only one job may run at a time. Use ``start()`` to launch, ``stop()`` to
    cancel, and ``get_state()`` to poll progress.
    """

    settings: Settings = field(default_factory=get_settings)
    state: BruteForceState = field(default_factory=BruteForceState)
    _thread: threading.Thread | None = field(default=None, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def start(
        self,
        *,
        start_length: int | None = None,
        start_from: str | None = None,
        headless: bool | None = None,
    ) -> str:
        """Launch a new brute-force job in a background daemon thread.

        Args:
            start_length: Initial password length. Defaults to settings.start_length.
            start_from: Resume from this exact password. None = from the beginning.
            headless: Browser headless mode. Defaults to settings.headless.

        Returns:
            UUID string identifying the new job.

        Raises:
            RuntimeError: If a job is already running.
        """
        with self._lock:
            if self.state.status == JobStatus.RUNNING:
                raise RuntimeError("A brute-force job is already running")

            job_id = str(uuid.uuid4())
            self._stop_event.clear()
            self.state = BruteForceState(
                job_id=job_id,
                status=JobStatus.RUNNING,
                current_length=start_length or self.settings.start_length,
                started_at=datetime.now(UTC),
            )

            # API/request overrides take priority; fall back to .env defaults
            effective_start_from = start_from if start_from is not None else self.settings.start_from
            effective_headless = headless if headless is not None else self.settings.headless

            self._thread = threading.Thread(
                target=self._run,
                args=(self.state.current_length, effective_start_from, effective_headless),
                daemon=True,
                name=f"brute-force-{job_id[:8]}",
            )
            self._thread.start()
            return job_id

    def stop(self) -> None:
        """Signal the running job to stop after the current attempt finishes."""
        self._stop_event.set()

    def get_state(self) -> BruteForceState:
        """Return a copy of the current job state (safe to read from any thread)."""
        with self._lock:
            return BruteForceState(**self.state.__dict__)

    def _run(self, length: int, start_from: str | None, headless: bool) -> None:
        """Core brute-force loop — runs inside the background thread.

        Logic:
            1. Open a single Chromium browser and reuse one page.
            2. For each password length, iterate tiered_combinations().
            3. If start_from is set, skip all combos until that value is reached.
            4. On success → mark COMPLETED and exit.
            5. When all combos for a length are exhausted → increment length.
            6. On stop signal → mark STOPPED and exit.
        """
        skipping = bool(start_from)
        login_tester = LoginTester(self.settings)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=headless)
                page = browser.new_page()

                # Outer loop: increase password length until success or stop
                while not self._stop_event.is_set():
                    logger.info("Trying passwords of length %s", length)
                    self.state.current_length = length

                    if skipping and start_from and len(start_from) == length:
                        logger.info("Resuming from: %s", start_from)

                    # Inner loop: try every combination for the current length
                    for combo in tiered_combinations(self.settings, length):
                        if self._stop_event.is_set():
                            break

                        # Resume mode: fast-forward to the saved password
                        if skipping:
                            if combo != start_from:
                                continue
                            skipping = False
                            logger.info("Reached resume point: %s", combo)

                        self.state.last_password = combo
                        success = login_tester.try_password(page, combo)

                        if success:
                            self.state.found_password = combo
                            self.state.status = JobStatus.COMPLETED
                            self.state.message = f"Password found: {combo}"
                            self.state.finished_at = datetime.now(UTC)
                            logger.info("Found password: %s", combo)
                            browser.close()
                            return

                        self.state.tried_count += 1
                        if self.state.tried_count % self.settings.progress_log_interval == 0:
                            logger.info("Tried %s passwords", self.state.tried_count)

                    if self._stop_event.is_set():
                        break

                    # All combos for this length failed — move to next length
                    skipping = False
                    logger.info(
                        "Completed all length-%s combinations. Trying length %s...",
                        length,
                        length + 1,
                    )
                    length += 1

                browser.close()

            if self._stop_event.is_set():
                self.state.status = JobStatus.STOPPED
                self.state.message = "Job stopped by user"
            else:
                self.state.status = JobStatus.COMPLETED
                self.state.message = "All combinations exhausted without success"

        except Exception as exc:
            logger.exception("Brute-force job failed")
            self.state.status = JobStatus.FAILED
            self.state.message = str(exc)
        finally:
            self.state.finished_at = datetime.now(UTC)


# Module-level singleton shared by API and CLI
_runner = BruteForceRunner()


def get_brute_force_runner() -> BruteForceRunner:
    """Return the global BruteForceRunner instance."""
    return _runner
