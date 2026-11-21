"""Thread-safe In-Memory repository adapter.

Pre-seeded with realistic municipal demo issues, supporting lazy
image loading, search filtering, and cursor pagination.
"""

import asyncio
from typing import Any

from app.domain.models import Issue
from app.repositories.base import IssueRepository
from app.repositories.seed import generate_seed_issues


def _matches_filter(
    it: Issue,
    status: str | None,
    category: str | None,
    priority: str | None,
    department: str | None,
    search_term: str | None,
) -> bool:
    """Evaluate whether an Issue matches the given criteria."""
    if status and it.status.lower() != status.lower():
        return False
    if category and it.category.lower() != category.lower():
        return False
    if priority and it.priority_level.lower() != priority.lower():
        return False
    if department and it.department.lower() != department.lower():
        return False
    if search_term:
        searchable = f"{it.ticket_id} {it.title} {it.description} {it.address or ''}".lower()
        if search_term not in searchable:
            return False
    return True


def _paginate_items(items: list[Issue], limit: int, cursor: str | None) -> tuple[list[Issue], str | None]:
    """Slice items based on cursor ticket_id and limit."""
    start_idx = 0
    if cursor:
        for idx, it in enumerate(items):
            if it.ticket_id == cursor:
                start_idx = idx + 1
                break

    page = items[start_idx : start_idx + limit]
    has_more = len(page) == limit and (start_idx + limit) < len(items)
    next_cursor = page[-1].ticket_id if has_more else None
    return page, next_cursor


class InMemoryRepository(IssueRepository):
    """In-memory issue repository implementation."""

    def __init__(self, city_name: str = "Coimbatore") -> None:
        self._lock = asyncio.Lock()
        self._issues: dict[str, Issue] = {}
        self._photos: dict[str, str] = {}
        seeds = generate_seed_issues(city_name)
        for issue in seeds:
            self._issues[issue.ticket_id] = issue

    async def save_issue(self, issue: Issue) -> None:
        """Save a new issue in memory."""
        async with self._lock:
            self._issues[issue.ticket_id] = issue

    async def get_issue_by_id(self, ticket_id: str) -> Issue | None:
        """Fetch an issue by ticket_id."""
        async with self._lock:
            return self._issues.get(ticket_id)

    async def list_issues(
        self,
        status: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        department: str | None = None,
        search: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Issue], str | None]:
        """Filter, sort, and paginate issues."""
        async with self._lock:
            items = list(self._issues.values())

        items.sort(key=lambda x: (x.priority_score, x.created_at), reverse=True)
        search_term = search.lower().strip() if search else None
        filtered = [
            it for it in items
            if _matches_filter(it, status, category, priority, department, search_term)
        ]
        return _paginate_items(filtered, limit, cursor)

    async def update_issue(self, issue: Issue) -> None:
        """Update existing issue in memory."""
        async with self._lock:
            self._issues[issue.ticket_id] = issue

    async def save_photo(self, ticket_id: str, photo_data_url: str) -> None:
        """Store compressed photo lazily."""
        async with self._lock:
            self._photos[ticket_id] = photo_data_url
            issue = self._issues.get(ticket_id)
            if issue:
                issue.has_photo = True

    async def get_photo(self, ticket_id: str) -> str | None:
        """Retrieve stored photo data URL."""
        async with self._lock:
            return self._photos.get(ticket_id)

    async def get_all_raw(self) -> list[dict[str, Any]]:
        """Return raw dictionary representations for aggregation queries."""
        async with self._lock:
            return [it.to_dict() for it in self._issues.values()]
