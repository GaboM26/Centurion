"""Normalized order result model for Centurion."""

from dataclasses import dataclass, field
from typing import Any, Mapping


def _normalize_optional_string(value: object) -> str | None:
    """Return a stripped string when a value is present."""
    if value is None:
        return None

    normalized_value = str(value).strip()
    return normalized_value or None


def _normalize_required_string(value: object, field_name: str) -> str:
    """Return a required stripped string or raise when absent."""
    normalized_value = _normalize_optional_string(value)
    if normalized_value is None:
        raise ValueError(f"{field_name} must not be blank.")

    return normalized_value


@dataclass(slots=True)
class OrderResult:
    """Normalized order payload returned by Centurion clients."""

    order_id: str
    client_order_id: str
    ticker: str
    status: str
    trade_type: str | None = None
    initial_count: str | None = None
    remaining_count: str | None = None
    fill_count: str | None = None
    created_time: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.order_id = _normalize_required_string(self.order_id, "order_id")
        self.client_order_id = _normalize_required_string(
            self.client_order_id,
            "client_order_id",
        )
        self.ticker = _normalize_required_string(self.ticker, "ticker")
        self.status = _normalize_required_string(self.status, "status")
        self.trade_type = _normalize_optional_string(self.trade_type)
        self.initial_count = _normalize_optional_string(self.initial_count)
        self.remaining_count = _normalize_optional_string(self.remaining_count)
        self.fill_count = _normalize_optional_string(self.fill_count)
        self.created_time = _normalize_optional_string(self.created_time)

    @classmethod
    def from_api_response(cls, payload: Mapping[str, Any]) -> "OrderResult":
        """Build an OrderResult from a Kalshi order response or order payload."""
        nested_order = payload.get("order")

        if isinstance(nested_order, Mapping):
            order_payload = dict(nested_order)
        else:
            order_payload = dict(payload)

        if not order_payload:
            raise ValueError("order payload must not be empty.")

        return cls(
            order_id=order_payload.get("order_id"),
            client_order_id=order_payload.get("client_order_id"),
            ticker=order_payload.get("ticker"),
            status=order_payload.get("status"),
            trade_type=(
                _normalize_optional_string(order_payload.get("book_side"))
                or _normalize_optional_string(order_payload.get("side"))
            ),
            initial_count=order_payload.get("initial_count_fp"),
            remaining_count=order_payload.get("remaining_count_fp"),
            fill_count=order_payload.get("fill_count_fp"),
            created_time=order_payload.get("created_time"),
            raw=dict(order_payload),
        )
