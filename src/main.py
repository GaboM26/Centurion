"""Centurion entry point for ad hoc local model and config checks."""

from __future__ import annotations

import argparse
import sys

from config import get_settings
from utils.menu import preview_event_order, preview_order_result, print_settings_summary, run_test_menu


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface for local checks."""
    parser = argparse.ArgumentParser(description="Run Centurion local checks.")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("config", "preview-order", "preview-result"),
        help="Local check to run.",
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Run the interactive local tester menu.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run Centurion local checks."""
    args = _build_parser().parse_args(argv)
    settings = get_settings()

    try:
        should_run_menu = (
            sys.stdin.isatty()
            and settings.app.enable_test_menu
            and (args.menu or args.command is None)
        )

        if should_run_menu:
            return run_test_menu()

        if args.menu and not sys.stdin.isatty():
            raise RuntimeError("The interactive test menu requires a TTY.")

        command = args.command or "config"

        if command == "config":
            print_settings_summary()
        elif command == "preview-order":
            preview_event_order()
        else:
            preview_order_result()
        return 0
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nExiting Centurion.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
