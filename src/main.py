"""Centurion entry point for ad hoc Kalshi trading tests."""

import sys

from utils.common import log_startup, setup_logging, setup_path
from utils.common.logger import logger

setup_path()
setup_logging()

from clients.kalshi import KalshiApiError, KalshiTradeClient
from config import get_settings
from utils.common.menu import run_trade_menu


def main() -> None:
    """Run the interactive Centurion trade menu."""
    log_startup()
    settings = get_settings()
    client = KalshiTradeClient(settings.kalshi)

    try:
        run_trade_menu(client=client, settings=settings)
    except KeyboardInterrupt:
        logger.info("Exiting Centurion.")
    except KalshiApiError as exc:
        logger.error("Kalshi API error: %s", exc)
        sys.exit(1)
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected Centurion failure: %s", exc)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
