"""Tests for authentication, constant-time compare, and HMAC tokens."""

import time

from app.services.auth import AuthService


def test_auth_constant_time_password_verification():
    """Verify correct password matches and wrong passwords fail."""
    auth = AuthService("secret-password-123", "secret-token-key-32-bytes-long")
    assert auth.verify_password("secret-password-123") is True
    assert auth.verify_password("wrong-password") is False
    assert auth.verify_password("") is False


def test_session_token_lifecycle():
    """Verify token generation and validation."""
    auth = AuthService("admin-pwd", "secret-key-32-bytes-long")
    token = auth.create_session_token("admin")
    assert token is not None
    assert auth.verify_session_token(token) is True


def test_session_token_tampered():
    """Verify tampered tokens are rejected."""
    auth = AuthService("admin-pwd", "secret-key-32-bytes-long")
    token = auth.create_session_token("admin")
    parts = token.split(":")
    tampered = f"{parts[0]}:{parts[1]}:badsignature"
    assert auth.verify_session_token(tampered) is False


def test_session_token_expired():
    """Verify expired tokens are rejected."""
    auth = AuthService("admin-pwd", "secret-key-32-bytes-long")
    # Fabricate expired timestamp
    past_timestamp = int(time.time()) - 100
    payload = f"admin:{past_timestamp}"
    import hashlib
    import hmac
    sig = hmac.new(
        b"secret-key-32-bytes-long",
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    expired_token = f"{payload}:{sig}"

    assert auth.verify_session_token(expired_token) is False
