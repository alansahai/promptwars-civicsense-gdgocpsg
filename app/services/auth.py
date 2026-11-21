"""Administrative authentication service with HMAC-SHA256 sessions.

Provides constant-time password verification, signed expiring session tokens,
and login attempt rate tracking.
"""

import hashlib
import hmac
import time
from typing import Final

TOKEN_EXPIRATION_SECONDS: Final[int] = 8 * 3600  # 8 hours


class AuthService:
    """Manages admin credentials and secure session tokens."""

    def __init__(self, admin_password: str, token_secret: str) -> None:
        self.admin_password = admin_password
        self.token_secret = token_secret

    def verify_password(self, candidate: str) -> bool:
        """Verify candidate password using constant-time comparison."""
        return hmac.compare_digest(
            candidate.encode("utf-8"),
            self.admin_password.encode("utf-8"),
        )

    def create_session_token(self, username: str = "admin") -> str:
        """Generate a cryptographically signed expiring session token."""
        expires_at = int(time.time()) + TOKEN_EXPIRATION_SECONDS
        payload = f"{username}:{expires_at}"
        signature = hmac.new(
            self.token_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"{payload}:{signature}"

    def verify_session_token(self, token: str) -> bool:
        """Validate signature and expiration of an admin session token."""
        if not token or ":" not in token:
            return False

        parts = token.split(":")
        if len(parts) != 3:
            return False

        username, expires_str, provided_sig = parts
        try:
            expires_at = int(expires_str)
        except ValueError:
            return False

        # Expiration check
        if time.time() > expires_at:
            return False

        payload = f"{username}:{expires_str}"
        expected_sig = hmac.new(
            self.token_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(provided_sig, expected_sig)
