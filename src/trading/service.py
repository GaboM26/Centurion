"""Kalshi trading helpers and execution pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from constants.orders import (
    DEFAULT_SELF_TRADE_PREVENTION_TYPE,
    VALID_SELF_TRADE_PREVENTION_TYPE,
)
from models import EventOrderRequest, OrderResult
from trading.client import KalshiApiError, KalshiRestClient


@dataclass(frozen=True, slots=True)
class TradeExecutionContext:
    """Prepared trade execution context."""

    request: EventOrderRequest
    payload: dict[str, Any]


class KalshiTradingService:
    """High-level Kalshi trading helpers for Centurion."""

    def __init__(
        self,
        client: KalshiRestClient | None = None,
        *,
        self_trade_prevention_type: str = DEFAULT_SELF_TRADE_PREVENTION_TYPE,
        validation_attempts: int = 5,
        validation_poll_interval: float = 0.25,
    ) -> None:
        if self_trade_prevention_type not in VALID_SELF_TRADE_PREVENTION_TYPE:
            raise ValueError("self_trade_prevention_type is invalid.")

        if validation_attempts < 1:
            raise ValueError("validation_attempts must be at least 1.")
        if validation_poll_interval < 0:
            raise ValueError("validation_poll_interval must not be negative.")

        self.client = client or KalshiRestClient()
        self.self_trade_prevention_type = self_trade_prevention_type
        self.validation_attempts = validation_attempts
        self.validation_poll_interval = validation_poll_interval

    def preTradeWrites(self, order_request: EventOrderRequest) -> TradeExecutionContext:
        """Prepare the outbound Kalshi payload for a trade."""
        return TradeExecutionContext(
            request=order_request,
            payload=self._build_event_order_payload(order_request),
        )

    def placeTrade(self, context: TradeExecutionContext) -> Mapping[str, Any]:
        """Place the prepared event order through the V2 endpoint."""
        response = self.client.post(
            "/portfolio/events/orders",
            json_body=context.payload,
        )
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid create-order response.")
        return response

    def validate(self, context: TradeExecutionContext, placement: Mapping[str, Any]) -> OrderResult:
        """Validate a placed order by fetching the normalized order record."""
        order_id = self._required_string(placement.get("order_id"), "order_id")
        placement_ts_ms = self._optional_int(placement.get("ts_ms"))

        if placement_ts_ms is not None:
            self._wait_for_user_data_sync(placement_ts_ms)

        last_error: KalshiApiError | None = None
        for attempt in range(self.validation_attempts):
            try:
                order = self.get_order(order_id)
            except KalshiApiError as exc:
                last_error = exc
                if exc.status_code == 404 and attempt + 1 < self.validation_attempts:
                    time.sleep(self.validation_poll_interval)
                    continue
                if exc.status_code == 404:
                    raise RuntimeError(
                        "Kalshi accepted the order write, but the order read model still "
                        "did not expose the order after validation retries."
                    ) from exc
                raise

            if order.client_order_id != context.request.client_order_id:
                raise RuntimeError(
                    "Validated order client_order_id did not match the submitted request."
                )

            return order

        if last_error is not None:
            raise last_error

        raise RuntimeError(f"Unable to validate order {order_id}.")

    def execute_trade(self, order_request: EventOrderRequest) -> OrderResult:
        """Run the full Centurion trade lifecycle for an event order."""
        context = self.preTradeWrites(order_request)
        placement = self.placeTrade(context)
        return self.validate(context, placement)

    def place_event_order(self, order_request: EventOrderRequest) -> OrderResult:
        """Convenience wrapper for executing a single event trade."""
        return self.execute_trade(order_request)

    def get_order(self, order_id: str) -> OrderResult:
        """Fetch and normalize a single order."""
        normalized_order_id = self._required_string(order_id, "order_id")
        response = self.client.get(f"/portfolio/orders/{normalized_order_id}")
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid get-order response.")
        return OrderResult.from_api_response(response)

    def list_orders(self, *, params: Mapping[str, Any] | None = None) -> list[OrderResult]:
        """Fetch and normalize the current order list."""
        response = self.client.get("/portfolio/orders", params=params)
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid list-orders response.")

        raw_orders = response.get("orders")
        if raw_orders is None:
            return []
        if not isinstance(raw_orders, list):
            raise RuntimeError("Kalshi returned an invalid orders collection.")

        return [
            OrderResult.from_api_response(order_payload)
            for order_payload in raw_orders
            if isinstance(order_payload, Mapping)
        ]

    def cancel_order(self, order_id: str) -> Mapping[str, Any]:
        """Cancel an event order through the V2 endpoint."""
        normalized_order_id = self._required_string(order_id, "order_id")
        response = self.client.delete(f"/portfolio/events/orders/{normalized_order_id}")
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid cancel-order response.")
        return dict(response)

    def decrease_order(self, order_id: str, reduce_count: str) -> Mapping[str, Any]:
        """Decrease an existing V2 event order."""
        normalized_order_id = self._required_string(order_id, "order_id")
        normalized_reduce_count = self._required_string(reduce_count, "reduce_count")
        response = self.client.post(
            f"/portfolio/events/orders/{normalized_order_id}/decrease",
            json_body={"reduce_count": normalized_reduce_count},
        )
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid decrease-order response.")
        return dict(response)

    def amend_order(
        self,
        order_id: str,
        *,
        price: str | None = None,
        count: str | None = None,
    ) -> Mapping[str, Any]:
        """Amend an existing V2 event order."""
        normalized_order_id = self._required_string(order_id, "order_id")
        amendment: dict[str, str] = {}
        if price is not None:
            amendment["price"] = self._required_string(price, "price")
        if count is not None:
            amendment["count"] = self._required_string(count, "count")
        if not amendment:
            raise ValueError("At least one amendment field must be provided.")

        response = self.client.post(
            f"/portfolio/events/orders/{normalized_order_id}/amend",
            json_body=amendment,
        )
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid amend-order response.")
        return dict(response)

    def get_balance(self) -> Mapping[str, Any]:
        """Fetch the portfolio balance payload."""
        response = self.client.get("/portfolio/balance")
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid balance response.")
        return dict(response)

    def get_positions(self, *, params: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        """Fetch the portfolio positions payload."""
        response = self.client.get("/portfolio/positions", params=params)
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid positions response.")
        return dict(response)

    def get_fills(self, *, params: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        """Fetch the portfolio fills payload."""
        response = self.client.get("/portfolio/fills", params=params)
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid fills response.")
        return dict(response)

    def get_user_data_timestamp(self) -> Mapping[str, Any]:
        """Fetch the exchange user-data timestamp payload."""
        response = self.client.get("/exchange/user_data_timestamp")
        if not isinstance(response, Mapping):
            raise RuntimeError("Kalshi returned an invalid user-data timestamp response.")
        return dict(response)

    def _build_event_order_payload(self, order_request: EventOrderRequest) -> dict[str, Any]:
        return {
            "ticker": order_request.ticker,
            "client_order_id": order_request.client_order_id,
            "side": order_request.trade_type,
            "count": order_request.count,
            "price": order_request.price,
            "time_in_force": order_request.time_in_force,
            "cancel_order_on_pause": order_request.cancel_order_on_pause,
            "self_trade_prevention_type": self.self_trade_prevention_type,
        }

    def _wait_for_user_data_sync(self, placement_ts_ms: int) -> None:
        target_time = datetime.fromtimestamp(placement_ts_ms / 1000, tz=timezone.utc)

        for attempt in range(self.validation_attempts):
            user_data = self.get_user_data_timestamp()
            as_of_time = self._parse_user_data_timestamp(user_data.get("as_of_time"))
            if as_of_time is not None and as_of_time >= target_time:
                return

            if attempt + 1 < self.validation_attempts:
                time.sleep(self.validation_poll_interval)

    def _parse_user_data_timestamp(self, value: object) -> datetime | None:
        normalized_value = str(value).strip() if value is not None else ""
        if not normalized_value:
            return None

        try:
            return datetime.fromisoformat(normalized_value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _optional_int(self, value: object) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _required_string(self, value: object, field_name: str) -> str:
        normalized_value = str(value).strip() if value is not None else ""
        if not normalized_value:
            raise ValueError(f"{field_name} must not be blank.")
        return normalized_value
