"""Repository factory providing store instance based on environment.

Instantiates either InMemoryRepository or UpstashRedisRepository based on
runtime settings and exposes repository reset for test isolation.
"""

from app.config import get_settings
from app.repositories.base import IssueRepository
from app.repositories.memory import InMemoryRepository
from app.repositories.upstash import UpstashRedisRepository


class _RepositoryHolder:
    """Internal holder for singleton repository instance."""

    instance: IssueRepository | None = None


def get_repository() -> IssueRepository:
    """Return configured IssueRepository singleton."""
    if _RepositoryHolder.instance is None:
        settings = get_settings()
        if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
            _RepositoryHolder.instance = UpstashRedisRepository(
                rest_url=settings.upstash_redis_rest_url,
                rest_token=settings.upstash_redis_rest_token,
            )
        else:
            _RepositoryHolder.instance = InMemoryRepository(city_name=settings.city_name)
    return _RepositoryHolder.instance


def reset_repository() -> None:
    """Reset repository instance (primarily for test isolation)."""
    _RepositoryHolder.instance = None
