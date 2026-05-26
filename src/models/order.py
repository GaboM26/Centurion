"""Core event order contract for Centurion."""

from dataclasses import dataclass, field
from uuid import uuid4

from constants.orders import (
    DEFAULT_TIME_IN_FORCE,
    VALID_TIME_IN_FORCE,
    VALID_TRADE_TYPE,
)


@dataclass(slots=True)
class EventOrderRequest:
    """Centurion's minimal V2 event order request."""

    # Future optional fields may include expiration_time, post_only, reduce_only,
    # subaccount, order_group_id, and exchange_index.
    ticker: str
    trade_type: str
    price: str
    count: str
    description: str
    time_in_force: str = DEFAULT_TIME_IN_FORCE
    cancel_order_on_pause: bool = True
    client_order_id: str = field(
        default_factory=lambda: f"centurion-{uuid4()}",
    )

    def __post_init__(self) -> None:
        self.ticker = self.ticker.strip()
        self.price = self.price.strip()
        self.count = self.count.strip()
        self.description = self.description.strip()
        self.client_order_id = self.client_order_id.strip()

        if not self.ticker:
            raise ValueError("ticker must not be blank.")
        if self.trade_type not in VALID_TRADE_TYPE:
            raise ValueError("trade_type must be 'bid' or 'ask'.")
        if not self.price:
            raise ValueError("price must not be blank.")
        if not self.count:
            raise ValueError("count must not be blank.")
        if not self.description:
            raise ValueError("description must not be blank.")
        if self.time_in_force not in VALID_TIME_IN_FORCE:
            raise ValueError("time_in_force is invalid.")
        if not self.client_order_id:
            raise ValueError("client_order_id must not be blank.")
