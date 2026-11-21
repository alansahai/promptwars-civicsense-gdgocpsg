"""Storage repository protocol defining data access interfaces."""

from typing import Any, Protocol

from app.domain.models import Issue


class IssueRepository(Protocol):
    """Protocol for civic issue persistence stores."""

    async def save_issue(self, issue: Issue) -> None:
        """Persist a new civic issue record."""
        ...

    async def get_issue_by_id(self, ticket_id: str) -> Issue | None:
        """Retrieve an issue by its unique ticket identifier."""
        ...

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
        """List issues matching filters with cursor-based pagination."""
        ...

    async def update_issue(self, issue: Issue) -> None:
        """Update an existing civic issue record."""
        ...

    async def save_photo(self, ticket_id: str, photo_data_url: str) -> None:
        """Store compressed image data URL separately from the main record."""
        ...

    async def get_photo(self, ticket_id: str) -> str | None:
        """Retrieve stored photo data URL lazily."""
        ...

    async def get_all_raw(self) -> list[dict[str, Any]]:
        """Retrieve all issues as raw dictionaries for stats and analytics."""
        ...
