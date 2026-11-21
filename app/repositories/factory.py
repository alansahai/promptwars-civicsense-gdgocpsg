"""Repository factory providing store instance based on environment."""


from app.config import get_settings
from app.repositories.base import IssueRepository
from app.repositories.memory import InMemoryRepository
from app.repositories.upstash import UpstashRedisRepository

_REPO_INSTANCE: IssueRepository | None = None


def get_repository() -> IssueRepository:
    """Return configured IssueRepository singleton."""
    global _REPO_INSTANCE
    if _REPO_INSTANCE is None:
        settings = get_settings()
        if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
            _REPO_INSTANCE = UpstashRedisRepository(
                rest_url=settings.upstash_redis_rest_url,
                rest_token=settings.upstash_redis_rest_token,
            )
        else:
            _REPO_INSTANCE = InMemoryRepository(city_name=settings.city_name)
    return _REPO_INSTANCE


def reset_repository() -> None:
    """Reset repository instance (primarily for test isolation)."""
    global _REPO_INSTANCE
    _REPO_INSTANCE = None
