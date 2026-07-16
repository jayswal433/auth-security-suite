"""Playwright-based login attempt service.

Handles form filling, success detection, and reCAPTCHA error recovery.
"""

import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from auth_security_suite.core.settings import Settings


class LoginTester:
    """Attempts a single login with a given password via Playwright.

    Success is determined by a dashboard URL redirect. On failure the service
    checks for known error messages and reloads the page when reCAPTCHA blocks
    the attempt.
    """

    def __init__(self, settings: Settings) -> None:
        """Store settings used for selectors, URLs, and timeouts."""
        self.settings = settings

    def try_password(self, page: Page, password: str) -> bool:
        """Fill the login form and return True if authentication succeeds.

        Flow:
            1. Navigate to the login page.
            2. Fill email and password fields, click Sign In.
            3. Wait for a dashboard URL redirect (success).
            4. On timeout, check for error messages (invalid creds / reCAPTCHA).
            5. Reload the page on reCAPTCHA errors so the next attempt starts clean.

        Args:
            page: An open Playwright page (reused across attempts).
            password: Candidate password to test.

        Returns:
            True if login succeeded (dashboard reached), False otherwise.
        """
        page.goto(self.settings.login_url)

        page.get_by_placeholder(self.settings.email_placeholder).fill(
            self.settings.login_email
        )
        page.locator("input[type='password']").fill(password)
        page.get_by_role("button", name=self.settings.sign_in_button_text).click()

        # --- Success path: wait for redirect to dashboard ---
        try:
            page.wait_for_url(
                re.compile(self.settings.dashboard_url_pattern),
                timeout=self.settings.nav_timeout_ms,
            )
            return True
        except PlaywrightTimeoutError:
            pass

        # --- Failure path: look for visible error messages ---
        error = page.get_by_text(
            re.compile(r"Invalid reCAPTCHA|Invalid email or password", re.I)
        )
        try:
            error.wait_for(state="visible", timeout=self.settings.error_timeout_ms)
            message = error.inner_text()

            # reCAPTCHA failure: reload so the next password gets a fresh page
            if re.search(r"recaptcha", message, re.I):
                page.reload()
                page.wait_for_load_state("domcontentloaded")
            return False
        except PlaywrightTimeoutError:
            pass

        # Fallback: check URL in case redirect happened without matching pattern
        return "dashboard" in page.url.lower()
