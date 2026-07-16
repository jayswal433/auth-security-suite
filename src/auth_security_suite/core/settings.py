"""Application configuration loaded from environment variables and .env files.

All settings use the ``AUTH_SECURITY_`` prefix. See ``.env.example`` for
available variables and defaults.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable runtime configuration for the auth security suite.

    Values are read from environment variables and an optional ``.env`` file.
    Deploy-time secrets and target-site credentials belong here — not in code.
    """

    model_config = SettingsConfigDict(
        env_prefix="AUTH_SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Auth Security Suite"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Target login site ---
    base_url: str = "https://issuer-evrc.viitorcloud.in/auth"
    login_path: str = "/login"
    login_email: str = "manil.jayswal@viitor.cloud"
    email_placeholder: str = "everycred@example.com"
    sign_in_button_text: str = "Sign In"
    dashboard_url_pattern: str = r".*/dashboard.*"

    # --- Brute-force behaviour ---
    start_length: int = Field(default=8, ge=1, description="Initial password length to try.")
    start_from: str | None = Field(
        default=None,
        description="Resume from this password. Empty/null starts from the beginning.",
    )
    headless: bool = True
    nav_timeout_ms: int = Field(default=8000, ge=1000, description="Dashboard redirect wait (ms).")
    error_timeout_ms: int = Field(default=3000, ge=500, description="Error message wait (ms).")
    progress_log_interval: int = Field(default=100, ge=1, description="Log every N attempts.")

    # --- Character sets for password generation ---
    digits: str = "0123456789"
    letters: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    special: str = "!@#$%^&*"

    @field_validator("start_from", mode="before")
    @classmethod
    def empty_start_from_is_none(cls, value: str | None) -> str | None:
        """Treat an empty .env value as 'start from the beginning'."""
        if value == "":
            return None
        return value

    @property
    def login_url(self) -> str:
        """Fully qualified login page URL built from base_url and login_path."""
        return f"{self.base_url.rstrip('/')}{self.login_path}"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton per process)."""
    return Settings()  # type: ignore[call-arg]
