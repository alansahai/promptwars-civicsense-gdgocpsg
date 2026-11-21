"""Typed domain exceptions for CivicResolve core operations.

Separates domain error semantics from HTTP status code representations.
"""


class CivicResolveError(Exception):
    """Base exception for all CivicResolve domain and service errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(CivicResolveError):
    """Raised when a requested resource (e.g. ticket) cannot be located."""


class InvalidTransitionError(CivicResolveError):
    """Raised when an issue lifecycle status transition violates rules."""


class ValidationError(CivicResolveError):
    """Raised when input parameters fail domain validation rules."""


class AuthError(CivicResolveError):
    """Raised when credentials or session tokens are invalid or expired."""


class UpstreamError(CivicResolveError):
    """Raised when an external service (LLM, Redis) fails persistently."""
