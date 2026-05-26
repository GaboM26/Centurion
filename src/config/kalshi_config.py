"""Configuration management for Centurion."""

from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from constants.kalshi import KALSHI_BASE_URL, KALSHI_DEMO_BASE_URL
from utils.paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")


class KalshiConfig(BaseSettings):
    """Kalshi API configuration settings."""

    demo: bool = Field(default=True, description="Use the Kalshi demo environment when True.")
    base_url: str = Field(
        default=KALSHI_BASE_URL,
        description="Kalshi trade API base URL. Auto-selected by the demo flag.",
    )
    api_key: str | None = Field(default=None, description="Kalshi API key.")
    api_secret: str | None = Field(default=None, description="Raw Kalshi PEM private key.")
    api_secret_path: str | None = Field(
        default=None,
        description="Path to the Kalshi PEM private key file.",
    )
    demo_api_key: str | None = Field(default=None, description="Demo Kalshi API key.")
    demo_api_secret: str | None = Field(default=None, description="Raw demo Kalshi PEM key.")
    demo_api_secret_path: str | None = Field(
        default=None,
        description="Path to the demo Kalshi PEM private key file.",
    )
    timeout: int = Field(default=30, description="HTTP timeout in seconds.")

    model_config = SettingsConfigDict(env_prefix="KALSHI_")

    def model_post_init(self, __context: object) -> None:
        """Apply demo overrides after settings are loaded."""
        if self.demo:
            object.__setattr__(self, "base_url", KALSHI_DEMO_BASE_URL)
            if self.demo_api_key:
                object.__setattr__(self, "api_key", self.demo_api_key)
            if self.demo_api_secret:
                object.__setattr__(self, "api_secret", self.demo_api_secret)
            if self.demo_api_secret_path:
                object.__setattr__(self, "api_secret_path", self.demo_api_secret_path)

    @property
    def resolved_api_secret(self) -> str | None:
        """Return the PEM content from api_secret or api_secret_path."""
        if self.api_secret:
            return self.api_secret.strip()

        if self.api_secret_path:
            secret_path = Path(self.api_secret_path).expanduser()
            if not secret_path.is_absolute():
                secret_path = PROJECT_ROOT / secret_path
            try:
                return secret_path.read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise RuntimeError(f"Failed to read API secret from {secret_path}: {exc}") from exc

        return None

    def load_private_key(self):
        """Load and return the RSA private key used to sign Kalshi requests."""
        pem_text = self.resolved_api_secret
        if not pem_text:
            raise RuntimeError(
                "No API secret configured. Set KALSHI_API_SECRET_PATH or KALSHI_API_SECRET."
            )

        try:
            return serialization.load_pem_private_key(
                pem_text.encode("utf-8"),
                password=None,
                backend=default_backend(),
            )
        except ValueError as exc:
            raise RuntimeError("Failed to deserialize Kalshi private key.") from exc


class LoggingConfig(BaseSettings):
    """Local logging configuration."""

    level: str = Field(default="INFO", description="Logging level.")
    format: str = Field(
        default="%(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        description="Local logging format string.",
    )
    log_file: str | None = Field(default=".logs/app.log", description="Optional log file path.")

    model_config = SettingsConfigDict(env_prefix="LOG_")


class Settings(BaseSettings):
    """Top-level settings container."""

    environment: str = Field(default="local", description="Runtime environment name.")
    kalshi: KalshiConfig = Field(default_factory=KalshiConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
