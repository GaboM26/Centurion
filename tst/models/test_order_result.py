"""Tests for the Centurion order result model."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from models import OrderResult


def test_order_result_from_nested_response_normalizes_core_fields() -> None:
    response = {
        "order": {
            "order_id": " order-123 ",
            "client_order_id": " client-123 ",
            "ticker": " KXBTC-TEST ",
            "status": " resting ",
            "book_side": " bid ",
            "initial_count_fp": "10.0000",
            "remaining_count_fp": "6.0000",
            "fill_count_fp": "4.0000",
            "created_time": " 2026-05-26T20:00:00Z ",
        }
    }

    result = OrderResult.from_api_response(response)

    assert result.order_id == "order-123"
    assert result.client_order_id == "client-123"
    assert result.ticker == "KXBTC-TEST"
    assert result.status == "resting"
    assert result.trade_type == "bid"
    assert result.initial_count == "10.0000"
    assert result.remaining_count == "6.0000"
    assert result.fill_count == "4.0000"
    assert result.created_time == "2026-05-26T20:00:00Z"
    assert result.raw["order_id"] == " order-123 "


def test_order_result_from_flat_payload_uses_legacy_side_when_needed() -> None:
    response = {
        "order_id": "order-123",
        "client_order_id": "client-123",
        "ticker": "KXBTC-TEST",
        "status": "executed",
        "side": "no",
    }

    result = OrderResult.from_api_response(response)

    assert result.trade_type == "no"


def test_order_result_requires_non_blank_identifiers() -> None:
    with pytest.raises(ValueError, match="order_id must not be blank."):
        OrderResult.from_api_response(
            {
                "order": {
                    "order_id": " ",
                    "client_order_id": "client-123",
                    "ticker": "KXBTC-TEST",
                    "status": "resting",
                }
            }
        )
