"""Kalshi request signing helpers."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from config import Settings, get_settings
from constants.kalshi import DEFAULT_USER_AGENT

KALSHI_ACCESS_KEY_HEADER = "KALSHI-ACCESS-KEY"
KALSHI_ACCESS_TIMESTAMP_HEADER = "KALSHI-ACCESS-TIMESTAMP"
KALSHI_ACCESS_SIGNATURE_HEADER = "KALSHI-ACCESS-SIGNATURE"


@dataclass(slots=True)
class KalshiAuthSigner:
    """Sign Kalshi REST requests with the configured RSA private key."""

    api_key: str
    private_key: object
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "KalshiAuthSigner":
        """Build a signer from application settings."""
        resolved_settings = settings or get_settings()
        api_key = (resolved_settings.kalshi.api_key or "").strip()
        if not api_key:
            raise RuntimeError(resolved_settings.kalshi.api_key_error_hint)

        return cls(
            api_key=api_key,
            private_key=resolved_settings.kalshi.load_private_key(),
        )

    def sign_request(self, method: str, path: str, timestamp_ms: str) -> str:
        """Return the base64-encoded Kalshi request signature."""
        message = f"{timestamp_ms}{method.upper()}{path}".encode("utf-8")
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("ascii")

    def build_headers(
        self,
        method: str,
        path: str,
        *,
        timestamp_ms: str | None = None,
        include_json_content_type: bool = False,
    ) -> dict[str, str]:
        """Build the signed Kalshi headers for a request."""
        resolved_timestamp = timestamp_ms or str(int(time.time() * 1000))
        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            KALSHI_ACCESS_KEY_HEADER: self.api_key,
            KALSHI_ACCESS_TIMESTAMP_HEADER: resolved_timestamp,
            KALSHI_ACCESS_SIGNATURE_HEADER: self.sign_request(
                method,
                path,
                resolved_timestamp,
            ),
        }

        if include_json_content_type:
            headers["Content-Type"] = "application/json"

        return headers
