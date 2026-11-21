"""High-level civic issue management service.

Implements core grievance management use-cases: issue creation, retrieval,
lifecycle transitions, administrative overrides, and re-analysis.
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.domain.errors import InvalidTransitionError, NotFoundError
from app.domain.lifecycle import can_transition
from app.domain.models import Issue, StatusHistoryItem
from app.repositories.base import IssueRepository
from app.services.analytics_service import AnalyticsService
from app.services.stats_service import StatsService
from app.services.triage import run_triage_pipeline


@dataclass(frozen=True)
class IssueDraft:
    """Parameters for constructing an initial citizen Issue record."""

    ticket_id: str
    title: str | None
    description: str
    address: str | None
    latitude: float | None
    longitude: float | None
    citizen_name: str | None
    has_photo: bool


def _generate_ticket_id() -> str:
    """Generate sequential-style ticket identifier e.g. CR-2026-00042."""
    year = datetime.now(UTC).year
    rand_num = secrets.randbelow(90000) + 10000
    return f"CR-{year}-{rand_num:05d}"


def _build_created_issue(draft: IssueDraft, triage: Any, now: datetime) -> Issue:
    """Assemble a new Issue domain model from draft and triage results."""
    final_title = draft.title.strip() if (draft.title and len(draft.title.strip()) > 5) else triage.analysis.suggested_title
    initial_history = [
        StatusHistoryItem(
            status="Reported",
            timestamp=now,
            author="Citizen",
            note="Grievance lodged via online portal",
        )
    ]
    return Issue(
        ticket_id=draft.ticket_id,
        title=final_title,
        description=draft.description,
        category=triage.final_category,
        department=triage.final_department,
        priority_level=triage.priority.level,
        priority_score=triage.priority.score,
        sla_hours=triage.priority.sla_hours,
        status="Reported",
        created_at=now,
        updated_at=now,
        address=draft.address,
        latitude=draft.latitude,
        longitude=draft.longitude,
        citizen_name=draft.citizen_name,
        has_photo=draft.has_photo,
        ai_analysis=triage.analysis,
        priority_breakdown=triage.priority.breakdown,
        status_history=initial_history,
        duplicate_of=triage.duplicates[0].ticket_id if triage.duplicates else None,
        admin_override=False,
        admin_notes=None,
    )


def _apply_overrides(
    issue: Issue,
    cat_override: str | None,
    pri_override: str | None,
    dept_override: str | None,
    dup_override: str | None,
) -> bool:
    """Apply administrative field overrides, returning True if any were applied."""
    is_override = False
    if cat_override and cat_override != issue.category:
        issue.category = cat_override
        is_override = True
    if pri_override and pri_override != issue.priority_level:
        issue.priority_level = pri_override
        is_override = True
    if dept_override and dept_override != issue.department:
        issue.department = dept_override
        is_override = True
    if dup_override:
        issue.duplicate_of = dup_override

    if is_override:
        issue.admin_override = True
    return is_override


def _record_status_transition(
    issue: Issue,
    new_status: str,
    author: str,
    note: str,
    is_override: bool,
    now: datetime,
) -> None:
    """Update issue status fields and append a new StatusHistoryItem."""
    issue.status = new_status
    issue.updated_at = now
    if new_status == "Resolved":
        issue.resolved_at = now

    history_note = note or f"Status shifted to {new_status}"
    if is_override:
        history_note += " (Admin override applied)"

    issue.status_history.append(
        StatusHistoryItem(
            status=new_status,
            timestamp=now,
            author=author,
            note=history_note,
            is_public=True,
        )
    )


class IssueService:
    """Use-case service for managing civic grievances."""

    def __init__(self, repository: IssueRepository) -> None:
        self.repo = repository
        self._stats_service = StatsService(repository)
        self._analytics_service = AnalyticsService(repository)

    async def create_issue(
        self,
        description: str,
        title: str | None = None,
        address: str | None = None,
        category: str | None = None,
        coords: tuple[float | None, float | None] = (None, None),
        citizen_name: str | None = None,
        photo_data_url: str | None = None,
        **kwargs: Any,
    ) -> tuple[Issue, list[Any]]:
        """Create and persist a new civic issue with automated triage."""
        lat = kwargs.get("latitude", coords[0])
        lon = kwargs.get("longitude", coords[1])
        existing_raw = await self.repo.get_all_raw()
        triage = await run_triage_pipeline(
            description, title, address, category, (lat, lon), photo_data_url, existing_raw
        )
        ticket_id = _generate_ticket_id()
        draft = IssueDraft(ticket_id, title, description, address, lat, lon, citizen_name, bool(photo_data_url))
        issue = _build_created_issue(draft, triage, datetime.now(UTC))

        await self.repo.save_issue(issue)
        if photo_data_url:
            await self.repo.save_photo(ticket_id, photo_data_url)

        return issue, triage.duplicates

    async def get_issue(self, ticket_id: str) -> Issue | None:
        """Fetch issue by ticket ID."""
        return await self.repo.get_issue_by_id(ticket_id)

    async def get_issue_photo(self, ticket_id: str) -> str | None:
        """Fetch lazy image for an issue."""
        return await self.repo.get_photo(ticket_id)

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
        """List issues with filtering and pagination."""
        return await self.repo.list_issues(
            status=status,
            category=category,
            priority=priority,
            department=department,
            search=search,
            limit=limit,
            cursor=cursor,
        )

    async def update_issue_status(
        self,
        ticket_id: str,
        new_status: str,
        author: str = "Admin Officer",
        note: str = "",
        overrides: tuple[str | None, str | None, str | None] = (None, None, None),
        duplicate_of: str | None = None,
        **kwargs: Any,
    ) -> Issue:
        """Update ticket status, apply administrative overrides, and update history."""
        issue = await self.repo.get_issue_by_id(ticket_id)
        if not issue:
            raise NotFoundError(f"Ticket {ticket_id} not found")

        if not can_transition(issue.status, new_status):
            raise InvalidTransitionError(f"Transition from {issue.status} to {new_status} is not permitted")

        cat_override = kwargs.get("category_override", overrides[0])
        pri_override = kwargs.get("priority_override", overrides[1])
        dept_override = kwargs.get("department_override", overrides[2])
        dup_override = kwargs.get("duplicate_of", duplicate_of)

        now = datetime.now(UTC)
        is_override = _apply_overrides(issue, cat_override, pri_override, dept_override, dup_override)
        _record_status_transition(issue, new_status, author, note, is_override, now)

        await self.repo.update_issue(issue)
        return issue

    async def reanalyze_issue(self, ticket_id: str) -> Issue:
        """Trigger re-analysis of an existing ticket."""
        issue = await self.repo.get_issue_by_id(ticket_id)
        if not issue:
            raise NotFoundError(f"Ticket {ticket_id} not found")

        photo_url = await self.repo.get_photo(ticket_id)
        existing_raw = await self.repo.get_all_raw()

        triage = await run_triage_pipeline(
            description=issue.description,
            title=issue.title,
            address=issue.address,
            user_category=issue.category,
            coords=(issue.latitude, issue.longitude),
            photo_data_url=photo_url,
            existing_issues=existing_raw,
        )

        issue.ai_analysis = triage.analysis
        issue.priority_score = triage.priority.score
        issue.priority_level = triage.priority.level
        issue.sla_hours = triage.priority.sla_hours
        issue.priority_breakdown = triage.priority.breakdown
        issue.updated_at = datetime.now(UTC)
        issue.status_history.append(
            StatusHistoryItem(
                status=issue.status,
                timestamp=datetime.now(UTC),
                author="System AI",
                note="Re-triage completed with updated model weights",
                is_public=False,
            )
        )
        await self.repo.update_issue(issue)
        return issue

    async def get_public_stats(self) -> dict[str, Any]:
        """Delegate public statistics calculation to StatsService."""
        return await self._stats_service.get_public_stats()

    async def get_admin_analytics(self) -> dict[str, Any]:
        """Delegate administrative analytics calculation to AnalyticsService."""
        return await self._analytics_service.get_admin_analytics()
