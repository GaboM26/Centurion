"""Signed Kalshi REST client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit

import requests

from config import Settings, get_settings
from trading.auth import KalshiAuthSigner


@dataclass(slots=True)
class KalshiApiError(RuntimeError):
    """Structured Kalshi API error."""

    status_code: int
    message: str
    code: str | None = None
    details: str | None = None
    service: str | None = None
    payload: Any = None

    def __str__(self) -> str:
        return f"Kalshi API error {self.status_code}: {self.message}"


class KalshiRestClient:
    """Perform signed REST requests against the Kalshi trade API."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        signer: KalshiAuthSigner | None = None,
        session: requests.Session | None = None,
    ) -> None:
        resolved_settings = settings or get_settings()
        self.base_url = resolved_settings.kalshi.base_url.rstrip("/")
        self.timeout = resolved_settings.kalshi.timeout
        self.signer = signer or KalshiAuthSigner.from_settings(resolved_settings)
        self.session = session or requests.Session()

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Perform a signed GET request."""
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> Any:
        """Perform a signed POST request."""
        return self.request("POST", path, params=params, json_body=json_body)

    def delete(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> Any:
        """Perform a signed DELETE request."""
        return self.request("DELETE", path, params=params, json_body=json_body)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> Any:
        """Perform a signed Kalshi request and parse the JSON response."""
        url = self._build_url(path)
        headers = self.signer.build_headers(
            method,
            self._signing_path(url),
            include_json_content_type=json_body is not None,
        )
        response = self.session.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=self.timeout,
        )

        if response.ok:
            if response.status_code == 204 or not response.content:
                return {}
            return self._parse_json_response(response)

        self._raise_api_error(response)

    def _build_url(self, path: str) -> str:
        cleaned_path = path.strip()
        if not cleaned_path:
            raise ValueError("path must not be blank.")

        if cleaned_path.startswith("http://") or cleaned_path.startswith("https://"):
            return cleaned_path

        return f"{self.base_url}/{cleaned_path.lstrip('/')}"

    def _signing_path(self, url: str) -> str:
        parsed = urlsplit(url)
        return parsed.path

    def _parse_json_response(self, response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError("Kalshi returned a non-JSON response.") from exc

    def _raise_api_error(self, response: requests.Response) -> None:
        payload: Any = None

        try:
            payload = response.json()
        except ValueError:
            message = response.text.strip() or "Request failed."
            raise KalshiApiError(status_code=response.status_code, message=message) from None

        if isinstance(payload, Mapping):
            message = str(payload.get("message") or "Request failed.")
            raise KalshiApiError(
                status_code=response.status_code,
                message=message,
                code=self._optional_string(payload.get("code")),
                details=self._optional_string(payload.get("details")),
                service=self._optional_string(payload.get("service")),
                payload=payload,
            ) from None

        raise KalshiApiError(
            status_code=response.status_code,
            message="Request failed.",
            payload=payload,
        ) from None

    def _optional_string(self, value: object) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None
