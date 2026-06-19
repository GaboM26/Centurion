"""Tests for Kalshi auth signing."""

import base64
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from trading.auth import (  # noqa: E402
    KALSHI_ACCESS_KEY_HEADER,
    KALSHI_ACCESS_SIGNATURE_HEADER,
    KALSHI_ACCESS_TIMESTAMP_HEADER,
    KalshiAuthSigner,
)


def test_build_headers_signs_expected_message() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    signer = KalshiAuthSigner(
        api_key="demo-key",
        private_key=private_key,
        user_agent="centurion-test",
    )

    headers = signer.build_headers(
        "POST",
        "/trade-api/v2/portfolio/events/orders",
        timestamp_ms="1712345678901",
        include_json_content_type=True,
    )

    signature = base64.b64decode(headers[KALSHI_ACCESS_SIGNATURE_HEADER])
    private_key.public_key().verify(
        signature,
        b"1712345678901POST/trade-api/v2/portfolio/events/orders",
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    assert headers[KALSHI_ACCESS_KEY_HEADER] == "demo-key"
    assert headers[KALSHI_ACCESS_TIMESTAMP_HEADER] == "1712345678901"
    assert headers["User-Agent"] == "centurion-test"
    assert headers["Content-Type"] == "application/json"
