"""FastAPI dependencies for authentication, rate limiting, and services."""

import time
from collections import defaultdict
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings, get_settings
from app.repositories.base import IssueRepository
from app.repositories.factory import get_repository
from app.services.analytics_service import AnalyticsService
from app.services.auth import AuthService
from app.services.issue_service import IssueService
from app.services.stats_service import StatsService


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter by client IP."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, ip_address: str) -> bool:
        """Check and update request timestamp log for client IP."""
        now = time.time()
        cutoff = now - self.window_seconds
        self.history[ip_address] = [t for t in self.history[ip_address] if t > cutoff]
        if len(self.history[ip_address]) >= self.max_requests:
            return False
        self.history[ip_address].append(now)
        return True


# Dedicated rate limiter instances
report_rate_limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=300)
login_rate_limiter = SlidingWindowRateLimiter(max_requests=6, window_seconds=300)
general_rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=60)


def client_ip(request: Request) -> str:
    """Extract verified client IP address handling Vercel and reverse-proxy headers."""
    vercel_ip = request.headers.get("x-vercel-forwarded-for")
    if vercel_ip:
        return vercel_ip.split(",")[0].strip()

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[0]

    return request.client.host if request.client else "127.0.0.1"


# Backward-compatible alias
get_client_ip = client_ip


def rate_limit_reports(request: Request) -> None:
    """Enforce rate limits on issue creation."""
    ip = client_ip(request)
    if not report_rate_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for issue submissions. Please wait 5 minutes.",
        )


def rate_limit_login(request: Request) -> None:
    """Enforce rate limits on administrative login attempts."""
    ip = client_ip(request)
    if not login_rate_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 5 minutes.",
        )


def get_auth_service(settings: Annotated[Settings, Depends(get_settings)]) -> AuthService:
    """Return configured AuthService instance."""
    return AuthService(
        admin_password=settings.admin_password,
        token_secret=settings.token_secret,
    )


def get_issue_service(repo: Annotated[IssueRepository, Depends(get_repository)]) -> IssueService:
    """Return configured IssueService."""
    return IssueService(repo)


def get_stats_service(repo: Annotated[IssueRepository, Depends(get_repository)]) -> StatsService:
    """Return configured StatsService."""
    return StatsService(repo)


def get_analytics_service(repo: Annotated[IssueRepository, Depends(get_repository)]) -> AnalyticsService:
    """Return configured AnalyticsService."""
    return AnalyticsService(repo)


def require_admin_auth(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> str:
    """Enforce admin authentication via cookie or Authorization header."""
    token = request.cookies.get("civic_session")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token or not auth_service.verify_session_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid administrator credentials or session required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # CSRF protection check on state-changing methods
    if request.method in {"POST", "PATCH", "DELETE"}:
        custom_header = request.headers.get("X-Civic-Admin") or request.headers.get("X-Requested-With")
        if not custom_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing custom CSRF defense header",
            )

    return "admin"
