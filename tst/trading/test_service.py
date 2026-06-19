"""Tests for the Kalshi trading service."""

import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from models import EventOrderRequest  # noqa: E402
from trading.auth import KalshiAuthSigner  # noqa: E402
from trading.client import KalshiRestClient  # noqa: E402
from trading.service import KalshiTradingService  # noqa: E402


class FakeResponse:
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)
        self.ok = 200 <= status_code < 300
        self.content = self.text.encode("utf-8")

    def json(self):
        return self._payload


class RecordingSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _build_service(*responses: FakeResponse) -> tuple[KalshiTradingService, RecordingSession]:
    session = RecordingSession(list(responses))
    client = KalshiRestClient(
        signer=KalshiAuthSigner(
            api_key="demo-key",
            private_key=rsa.generate_private_key(public_exponent=65537, key_size=2048),
        ),
        session=session,
    )
    service = KalshiTradingService(
        client=client,
        validation_attempts=2,
        validation_poll_interval=0,
    )
    return service, session


def test_pre_trade_writes_maps_event_order_request_to_v2_payload() -> None:
    service, _session = _build_service()
    request = EventOrderRequest(
        ticker="KXBTC-TEST",
        trade_type="bid",
        price="0.5500",
        count="10.00",
        description="Buy yes exposure",
    )

    context = service.preTradeWrites(request)

    assert context.payload == {
        "ticker": "KXBTC-TEST",
        "client_order_id": request.client_order_id,
        "side": "bid",
        "count": "10.00",
        "price": "0.5500",
        "time_in_force": "fill_or_kill",
        "cancel_order_on_pause": True,
        "self_trade_prevention_type": "taker_at_cross",
    }


def test_execute_trade_runs_place_and_validate_flow() -> None:
    service, session = _build_service(
        FakeResponse(
            201,
            {
                "order_id": "ord-123",
                "client_order_id": "client-123",
                "fill_count": "0.00",
                "remaining_count": "10.00",
                "ts_ms": 1712345678901,
            },
        ),
        FakeResponse(
            200,
            {
                "as_of_time": "2024-04-05T19:34:38.901000Z",
            },
        ),
        FakeResponse(
            200,
            {
                "order": {
                    "order_id": "ord-123",
                    "client_order_id": "client-123",
                    "ticker": "KXBTC-TEST",
                    "status": "resting",
                    "book_side": "bid",
                    "initial_count_fp": "10.00",
                    "remaining_count_fp": "10.00",
                    "fill_count_fp": "0.00",
                    "created_time": "2026-06-18T20:00:00Z",
                }
            },
        ),
    )
    request = EventOrderRequest(
        ticker="KXBTC-TEST",
        trade_type="bid",
        price="0.5500",
        count="10.00",
        description="Buy yes exposure",
        client_order_id="client-123",
    )

    result = service.execute_trade(request)

    assert result.order_id == "ord-123"
    assert result.client_order_id == "client-123"
    assert result.status == "resting"
    assert session.calls[0]["url"].endswith("/portfolio/events/orders")
    assert session.calls[1]["url"].endswith("/exchange/user_data_timestamp")
    assert session.calls[2]["url"].endswith("/portfolio/orders/ord-123")


def test_validate_waits_for_user_data_sync_before_retrying_order_lookup() -> None:
    service, session = _build_service(
        FakeResponse(
            201,
            {
                "order_id": "ord-123",
                "client_order_id": "client-123",
                "fill_count": "0.00",
                "remaining_count": "10.00",
                "ts_ms": 1712345678901,
            },
        ),
        FakeResponse(
            200,
            {
                "as_of_time": "2024-04-05T19:34:37.000000Z",
            },
        ),
        FakeResponse(
            200,
            {
                "as_of_time": "2024-04-05T19:34:38.901000Z",
            },
        ),
        FakeResponse(
            200,
            {
                "order": {
                    "order_id": "ord-123",
                    "client_order_id": "client-123",
                    "ticker": "KXBTC-TEST",
                    "status": "resting",
                    "book_side": "bid",
                    "initial_count_fp": "10.00",
                    "remaining_count_fp": "10.00",
                    "fill_count_fp": "0.00",
                    "created_time": "2026-06-18T20:00:00Z",
                }
            },
        ),
    )
    request = EventOrderRequest(
        ticker="KXBTC-TEST",
        trade_type="bid",
        price="0.5500",
        count="10.00",
        description="Buy yes exposure",
        client_order_id="client-123",
    )

    result = service.execute_trade(request)

    assert result.order_id == "ord-123"
    assert session.calls[1]["url"].endswith("/exchange/user_data_timestamp")
    assert session.calls[2]["url"].endswith("/exchange/user_data_timestamp")
    assert session.calls[3]["url"].endswith("/portfolio/orders/ord-123")
