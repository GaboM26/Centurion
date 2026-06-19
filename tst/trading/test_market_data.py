"""Tests for Kalshi market data helpers."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from trading.market_data import KalshiMarketDataClient  # noqa: E402


class FakeResponse:
    def __init__(self, status_code: int, payload) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


class RecordingSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.response


def test_get_market_snapshot_reads_quote_fields() -> None:
    session = RecordingSession(
        FakeResponse(
            200,
            {
                "market": {
                    "ticker": "KXBTC-TEST",
                    "title": "Bitcoin above target",
                    "status": "active",
                    "yes_bid_dollars": "0.5400",
                    "yes_ask_dollars": "0.5500",
                    "no_bid_dollars": "0.4500",
                    "no_ask_dollars": "0.4600",
                    "last_price_dollars": "0.5450",
                }
            },
        )
    )
    client = KalshiMarketDataClient(session=session)

    market = client.get_market_snapshot("KXBTC-TEST")

    assert market.ticker == "KXBTC-TEST"
    assert market.yes_ask_dollars == "0.5500"
    assert market.last_price_dollars == "0.5450"
    assert session.calls[0]["url"].endswith("/markets/KXBTC-TEST")
