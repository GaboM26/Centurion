"""Tests for the signed Kalshi REST client."""

import json
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from trading.auth import KalshiAuthSigner  # noqa: E402
from trading.client import KalshiApiError, KalshiRestClient  # noqa: E402


class FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.ok = 200 <= status_code < 300
        self.content = (
            json.dumps(payload).encode("utf-8")
            if payload is not None
            else text.encode("utf-8")
        )

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON payload.")
        return self._payload


class RecordingSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _build_client(*responses: FakeResponse) -> tuple[KalshiRestClient, RecordingSession]:
    session = RecordingSession(list(responses))
    signer = KalshiAuthSigner(
        api_key="demo-key",
        private_key=rsa.generate_private_key(public_exponent=65537, key_size=2048),
    )
    client = KalshiRestClient(
        signer=signer,
        session=session,
    )
    return client, session


def test_request_uses_signed_v2_path() -> None:
    client, session = _build_client(FakeResponse(200, {"ok": True}))

    response = client.post("/portfolio/events/orders", json_body={"ticker": "TEST"})

    assert response == {"ok": True}
    assert session.calls[0]["url"] == "https://demo-api.kalshi.co/trade-api/v2/portfolio/events/orders"
    headers = session.calls[0]["headers"]
    assert headers["KALSHI-ACCESS-KEY"] == "demo-key"
    assert headers["Content-Type"] == "application/json"


def test_request_raises_structured_api_error() -> None:
    client, _session = _build_client(
        FakeResponse(
            409,
            {
                "code": "order_conflict",
                "message": "Duplicate client order id.",
                "details": "client_order_id already exists",
                "service": "trade-api",
            },
        )
    )

    with pytest.raises(KalshiApiError) as exc_info:
        client.post("/portfolio/events/orders", json_body={"ticker": "TEST"})

    error = exc_info.value
    assert error.status_code == 409
    assert error.code == "order_conflict"
    assert error.details == "client_order_id already exists"
    assert error.service == "trade-api"
