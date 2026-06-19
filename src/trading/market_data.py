"""Kalshi market data helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import requests

from config import Settings, get_settings
from constants.kalshi import DEFAULT_USER_AGENT


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """Minimal market quote snapshot used by the interactive menu."""

    ticker: str
    title: str | None
    status: str
    yes_bid_dollars: str
    yes_ask_dollars: str
    no_bid_dollars: str
    no_ask_dollars: str
    last_price_dollars: str


class KalshiMarketDataClient:
    """Fetch public Kalshi market data for interactive tooling."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        session: requests.Session | None = None,
    ) -> None:
        resolved_settings = settings or get_settings()
        self.base_url = resolved_settings.kalshi.base_url.rstrip("/")
        self.timeout = resolved_settings.kalshi.timeout
        self.session = session or requests.Session()

    def get_market_snapshot(self, ticker: str) -> MarketSnapshot:
        """Fetch the current market quote snapshot for a ticker."""
        normalized_ticker = self._required_string(ticker, "ticker")
        response = self.session.get(
            f"{self.base_url}/markets/{normalized_ticker}",
            headers={
                "Accept": "application/json",
                "User-Agent": DEFAULT_USER_AGENT,
            },
            timeout=self.timeout,
        )

        if not response.ok:
            message = response.text.strip() or f"Failed to fetch market {normalized_ticker}."
            raise RuntimeError(message)

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("Kalshi returned a non-JSON market response.") from exc

        if not isinstance(payload, Mapping):
            raise RuntimeError("Kalshi returned an invalid market payload.")

        market = payload.get("market")
        if not isinstance(market, Mapping):
            raise RuntimeError("Kalshi market response did not contain a market object.")

        return MarketSnapshot(
            ticker=self._required_string(market.get("ticker"), "ticker"),
            title=self._optional_string(market.get("title")),
            status=self._required_string(market.get("status"), "status"),
            yes_bid_dollars=self._required_string(market.get("yes_bid_dollars"), "yes_bid_dollars"),
            yes_ask_dollars=self._required_string(market.get("yes_ask_dollars"), "yes_ask_dollars"),
            no_bid_dollars=self._required_string(market.get("no_bid_dollars"), "no_bid_dollars"),
            no_ask_dollars=self._required_string(market.get("no_ask_dollars"), "no_ask_dollars"),
            last_price_dollars=self._required_string(
                market.get("last_price_dollars"),
                "last_price_dollars",
            ),
        )

    def _required_string(self, value: object, field_name: str) -> str:
        normalized = self._optional_string(value)
        if normalized is None:
            raise RuntimeError(f"Kalshi market response is missing {field_name}.")
        return normalized

    def _optional_string(self, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None
