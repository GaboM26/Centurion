"""Tests for Kalshi credential guidance."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config.kalshi_config import KalshiConfig  # noqa: E402
from trading.auth import KalshiAuthSigner  # noqa: E402


def test_demo_mode_api_key_error_mentions_demo_variables() -> None:
    config = KalshiConfig(
        demo=True,
        api_key=None,
        demo_api_key=None,
        api_secret=None,
        api_secret_path=None,
        demo_api_secret=None,
        demo_api_secret_path=None,
    )

    assert "KALSHI_DEMO_API_KEY" in config.api_key_error_hint
    assert "KALSHI_API_KEY" in config.api_key_error_hint


def test_demo_mode_api_secret_error_mentions_demo_variables() -> None:
    config = KalshiConfig(
        demo=True,
        api_key=None,
        demo_api_key=None,
        api_secret=None,
        api_secret_path=None,
        demo_api_secret=None,
        demo_api_secret_path=None,
    )

    with pytest.raises(RuntimeError, match="KALSHI_DEMO_API_SECRET_PATH"):
        config.load_private_key()


def test_signer_from_settings_uses_mode_specific_key_hint() -> None:
    config = KalshiConfig(
        demo=True,
        api_key=None,
        demo_api_key=None,
        api_secret=None,
        api_secret_path=None,
        demo_api_secret=None,
        demo_api_secret_path=None,
    )

    class FakeSettings:
        kalshi = config

    with pytest.raises(RuntimeError, match="KALSHI_DEMO_API_KEY"):
        KalshiAuthSigner.from_settings(FakeSettings())
