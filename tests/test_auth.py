"""Tests for administrative HMAC authentication and session service."""

import hashlib
import hmac
import time

from app.services.auth import AuthService


def test_password_verification():
    """Verify constant-time password matching."""
    auth = AuthService("correct-password", "secret-key-32-bytes-long")
    assert auth.verify_password("correct-password") is True
    assert auth.verify_password("wrong-password") is False
    assert auth.verify_password("") is False


def test_session_token_lifecycle():
    """Verify creation and validation of HMAC session tokens."""
    auth = AuthService("admin-pwd", "secret-key-32-bytes-long")
    token = auth.create_session_token("admin")
    assert token is not None
    assert ":" in token

    # Verification must succeed
    assert auth.verify_session_token(token) is True

    # Tampered signature must fail
    tampered = token[:-4] + "abcd"
    assert auth.verify_session_token(tampered) is False


def test_session_token_expired():
    """Verify expired tokens are rejected."""
    auth = AuthService("admin-pwd", "secret-key-32-bytes-long")
    past_timestamp = int(time.time()) - 100
    payload = f"admin:{past_timestamp}"
    sig = hmac.new(
        b"secret-key-32-bytes-long",
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expired_token = f"{payload}:{sig}"

    assert auth.verify_session_token(expired_token) is False
