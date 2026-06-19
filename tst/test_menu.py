"""Tests for interactive menu utilities."""

import builtins
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import utils.menu as menu  # noqa: E402
from models import OrderResult  # noqa: E402


def test_build_test_menu_options_includes_trade_actions() -> None:
    options = menu.build_test_menu_options()

    assert [option.key for option in options] == ["1", "2", "3", "4", "5"]
    assert options[3].label == "Place demo event order"
    assert options[4].label == "Show recent orders"


def test_place_demo_event_order_runs_trade_pipeline(monkeypatch, capsys) -> None:
    prompts = iter(
        [
            "KXBTC-TEST",
            "10.00",
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(prompts))

    class FakeMarketDataClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def get_market_snapshot(self, ticker):
            assert ticker == "KXBTC-TEST"

            class Snapshot:
                ticker = "KXBTC-TEST"
                title = "Bitcoin above target"
                status = "active"
                yes_bid_dollars = "0.5400"
                yes_ask_dollars = "0.5500"
                no_bid_dollars = "0.4500"
                no_ask_dollars = "0.4600"
                last_price_dollars = "0.5450"

            return Snapshot()

    class FakeService:
        def place_event_order(self, order):
            assert order.ticker == "KXBTC-TEST"
            assert order.trade_type == "bid"
            assert order.price == "0.5500"
            assert order.description == "Menu demo buy YES on KXBTC-TEST at displayed ask 0.5500"
            return OrderResult(
                order_id="ord-123",
                client_order_id=order.client_order_id,
                ticker=order.ticker,
                status="resting",
                trade_type=order.trade_type,
                initial_count=order.count,
                remaining_count=order.count,
                fill_count="0.00",
                created_time="2026-06-18T20:00:00Z",
            )

    monkeypatch.setattr(menu, "KalshiMarketDataClient", FakeMarketDataClient)
    monkeypatch.setattr(menu, "KalshiTradingService", FakeService)

    menu.place_demo_event_order()

    captured = capsys.readouterr()
    assert "Current market quote" in captured.out
    assert "Placed order result" in captured.out
    assert "order_id: ord-123" in captured.out


def test_show_recent_orders_prints_normalized_orders(monkeypatch, capsys) -> None:
    monkeypatch.setattr(builtins, "input", lambda _prompt="": "")

    class FakeService:
        def list_orders(self, *, params=None):
            assert params == {"limit": "5"}
            return [
                OrderResult(
                    order_id="ord-123",
                    client_order_id="client-123",
                    ticker="KXBTC-TEST",
                    status="resting",
                    trade_type="bid",
                    remaining_count="10.00",
                )
            ]

    monkeypatch.setattr(menu, "KalshiTradingService", FakeService)

    menu.show_recent_orders()

    captured = capsys.readouterr()
    assert "Recent orders" in captured.out
    assert "order_id: ord-123" in captured.out
