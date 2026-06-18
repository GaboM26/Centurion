"""Interactive tester menu utilities for Centurion."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

from config import get_settings
from models import EventOrderRequest, OrderResult


def _bool_label(value: bool) -> str:
    return "yes" if value else "no"


def print_settings_summary() -> None:
    """Print the current runtime configuration summary."""
    settings = get_settings()
    print("\nCenturion configuration")
    print("-----------------------")
    print(f"environment:            {settings.environment}")
    print(f"demo mode:              {_bool_label(settings.kalshi.demo)}")
    print(f"base url:               {settings.kalshi.base_url}")
    print(f"api key configured:     {_bool_label(bool(settings.kalshi.api_key))}")
    print(
        "api secret configured:  "
        f"{_bool_label(bool(settings.kalshi.resolved_api_secret))}"
    )
    print(f"log level:              {settings.logging.level}")
    print(f"test menu enabled:      {_bool_label(settings.app.enable_test_menu)}")
    print()


def _prompt_required(prompt: str) -> str:
    """Read a required value from stdin."""
    value = input(prompt).strip()
    if not value:
        raise ValueError(f"{prompt.strip(': ')} must not be blank.")
    return value


def preview_event_order() -> None:
    """Prompt for an order payload and display the normalized result."""
    print("\nCreate EventOrderRequest")
    print("------------------------")
    order = EventOrderRequest(
        ticker=_prompt_required("Ticker: "),
        trade_type=_prompt_required("Trade type (bid/ask): "),
        price=_prompt_required("Price: "),
        count=_prompt_required("Count: "),
        description=_prompt_required("Description: "),
        time_in_force=input("Time in force [fill_or_kill]: ").strip() or "fill_or_kill",
    )
    print("\nNormalized EventOrderRequest")
    print("----------------------------")
    for key, value in asdict(order).items():
        print(f"{key}: {value}")
    print()


def preview_order_result() -> None:
    """Show how a Kalshi order response is normalized."""
    print("\nSample OrderResult")
    print("------------------")
    sample_payload = {
        "order": {
            "order_id": " demo-order-123 ",
            "client_order_id": " centurion-demo-123 ",
            "ticker": " KXBTC-TEST ",
            "status": " resting ",
            "book_side": " bid ",
            "initial_count_fp": "10.0000",
            "remaining_count_fp": "10.0000",
            "fill_count_fp": "0.0000",
            "created_time": " 2026-06-09T18:30:00Z ",
        }
    }
    result = OrderResult.from_api_response(sample_payload)
    for key, value in asdict(result).items():
        print(f"{key}: {value}")
    print()


@dataclass(frozen=True, slots=True)
class MenuOption:
    """Single interactive tester option."""

    key: str
    label: str
    action: Callable[[], None]


def build_test_menu_options() -> tuple[MenuOption, ...]:
    """Return the supported interactive tester options."""
    return (
        MenuOption("1", "Show configuration summary", print_settings_summary),
        MenuOption("2", "Preview EventOrderRequest normalization", preview_event_order),
        MenuOption("3", "Preview OrderResult normalization", preview_order_result),
    )


def run_test_menu() -> int:
    """Run the interactive Centurion tester menu."""
    options = build_test_menu_options()
    valid_choices = {option.key: option for option in options}
    exit_choice = str(len(options) + 1)

    while True:
        print("Centurion menu")
        print("--------------")
        for option in options:
            print(f"{option.key}. {option.label}")
        print(f"{exit_choice}. Exit")

        choice = input("\nSelect an option: ").strip()
        print()

        if choice == exit_choice:
            print("Exiting Centurion.")
            return 0

        selected_option = valid_choices.get(choice)
        if selected_option is None:
            print(f"Invalid option. Choose 1, 2, 3, or {exit_choice}.\n")
            continue

        selected_option.action()
