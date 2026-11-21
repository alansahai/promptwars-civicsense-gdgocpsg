"""High-level civic issue management service.

Implements all primary application use-cases: issue creation, retrieval,
lifecycle management, administrative overrides, and statistical aggregations.
"""

import random
from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import get_settings
from app.domain.lifecycle import can_transition, is_sla_breached
from app.domain.models import Issue, StatusHistoryItem
from app.repositories.base import IssueRepository
from app.services.triage import run_triage_pipeline


def _generate_ticket_id() -> str:
    """Generate sequential-style ticket identifier e.g. CR-2026-00042."""
    year = datetime.now(UTC).year
    rand_num = random.randint(1000, 99999)
    return f"CR-{year}-{rand_num:05d}"


class IssueService:
    """Use-case service for managing civic grievances."""

    def __init__(self, repository: IssueRepository) -> None:
        self.repo = repository

    async def create_issue(
        self,
        description: str,
        title: str | None = None,
        address: str | None = None,
        category: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        citizen_name: str | None = None,
        photo_data_url: str | None = None,
    ) -> tuple[Issue, list[Any]]:
        """Create and persist a new civic issue with automated triage."""
        existing_raw = await self.repo.get_all_raw()

        # Execute automated triage pipeline
        triage = await run_triage_pipeline(
            description=description,
            title=title,
            address=address,
            user_category=category,
            latitude=latitude,
            longitude=longitude,
            photo_data_url=photo_data_url,
            existing_issues=existing_raw,
        )

        ticket_id = _generate_ticket_id()
        now = datetime.now(UTC)

        final_title = title.strip() if (title and len(title.strip()) > 5) else triage.analysis.suggested_title

        initial_history = [
            StatusHistoryItem(
                status="Reported",
                timestamp=now,
                author="Citizen",
                note="Grievance lodged via online portal",
            )
        ]

        issue = Issue(
            ticket_id=ticket_id,
            title=final_title,
            description=description,
            category=triage.final_category,
            department=triage.final_department,
            priority_level=triage.priority.level,
            priority_score=triage.priority.score,
            sla_hours=triage.priority.sla_hours,
            status="Reported",
            created_at=now,
            updated_at=now,
            address=address,
            latitude=latitude,
            longitude=longitude,
            citizen_name=citizen_name,
            has_photo=bool(photo_data_url),
            ai_analysis=triage.analysis,
            priority_breakdown=triage.priority.breakdown,
            status_history=initial_history,
            duplicate_of=triage.duplicates[0].ticket_id if triage.duplicates else None,
            admin_override=False,
            admin_notes=None,
        )

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
        category_override: str | None = None,
        priority_override: str | None = None,
        department_override: str | None = None,
        duplicate_of: str | None = None,
    ) -> Issue:
        """Update ticket status, apply administrative overrides, and update history."""
        issue = await self.repo.get_issue_by_id(ticket_id)
        if not issue:
            raise KeyError(f"Ticket {ticket_id} not found")

        if not can_transition(issue.status, new_status):
            raise ValueError(f"Transition from {issue.status} to {new_status} is not permitted")

        now = datetime.now(UTC)
        is_override = False

        if category_override and category_override != issue.category:
            issue.category = category_override
            is_override = True
        if priority_override and priority_override != issue.priority_level:
            issue.priority_level = priority_override
            is_override = True
        if department_override and department_override != issue.department:
            issue.department = department_override
            is_override = True

        if is_override:
            issue.admin_override = True

        if duplicate_of:
            issue.duplicate_of = duplicate_of

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

        await self.repo.update_issue(issue)
        return issue

    async def reanalyze_issue(self, ticket_id: str) -> Issue:
        """Trigger re-analysis of an existing ticket."""
        issue = await self.repo.get_issue_by_id(ticket_id)
        if not issue:
            raise KeyError(f"Ticket {ticket_id} not found")

        photo_url = await self.repo.get_photo(ticket_id)
        existing_raw = await self.repo.get_all_raw()

        triage = await run_triage_pipeline(
            description=issue.description,
            title=issue.title,
            address=issue.address,
            user_category=issue.category,
            latitude=issue.latitude,
            longitude=issue.longitude,
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
        """Compute aggregated public statistics and dashboard metrics."""
        raw_list = await self.repo.get_all_raw()
        total = len(raw_list)
        resolved = sum(1 for i in raw_list if i.get("status") == "Resolved")
        open_issues = sum(1 for i in raw_list if i.get("status") in {"Reported", "In Progress"})
        rate = round((resolved / total * 100), 1) if total > 0 else 0.0

        # Average resolution time
        durations = []
        for i in raw_list:
            if i.get("status") == "Resolved" and i.get("resolved_at") and i.get("created_at"):
                c = datetime.fromisoformat(i["created_at"])
                r = datetime.fromisoformat(i["resolved_at"])
                durations.append((r - c).total_seconds() / 3600.0)
        avg_res = round(sum(durations) / len(durations), 1) if durations else 24.0

        # Category breakdown
        category_counts: dict[str, int] = {}
        for i in raw_list:
            cat = i.get("category", "Other")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # 14-day trend
        today = datetime.now(UTC).date()
        trend_days = [(today - timedelta(days=d)).isoformat() for d in range(13, -1, -1)]
        trend_counts = dict.fromkeys(trend_days, 0)
        for i in raw_list:
            created_str = i.get("created_at", "")[:10]
            if created_str in trend_counts:
                trend_counts[created_str] += 1

        # Locality coordinates for scatter map
        map_points = []
        for i in raw_list:
            if i.get("latitude") and i.get("longitude"):
                map_points.append(
                    {
                        "ticket_id": i["ticket_id"],
                        "lat": i["latitude"],
                        "lon": i["longitude"],
                        "category": i["category"],
                        "priority": i["priority_level"],
                        "status": i["status"],
                        "title": i["title"],
                    }
                )

        settings = get_settings()
        return {
            "city_name": settings.city_name,
            "total_issues": total,
            "open_issues": open_issues,
            "resolved_issues": resolved,
            "resolution_rate_percent": rate,
            "average_resolution_hours": avg_res,
            "category_breakdown": category_counts,
            "trend_14_days": [{"date": d, "count": trend_counts[d]} for d in trend_days],
            "map_points": map_points,
            "storage_mode": "memory" if settings.is_in_memory_storage else "upstash",
        }

    async def get_admin_analytics(self) -> dict[str, Any]:
        """Compute advanced operational analytics for administrative monitoring."""
        raw_list = await self.repo.get_all_raw()
        dept_workload: dict[str, dict[str, int]] = {}
        overdue_tickets: list[dict[str, Any]] = []
        overrides_count = 0

        for i in raw_list:
            dept = i.get("department", "General Grievance")
            if dept not in dept_workload:
                dept_workload[dept] = {"total": 0, "open": 0, "resolved": 0}
            dept_workload[dept]["total"] += 1
            if i.get("status") in {"Reported", "In Progress"}:
                dept_workload[dept]["open"] += 1
            elif i.get("status") == "Resolved":
                dept_workload[dept]["resolved"] += 1

            if i.get("admin_override"):
                overrides_count += 1

            # Check SLA breach
            created = datetime.fromisoformat(i["created_at"])
            sla = i.get("sla_hours", 48)
            resolved = datetime.fromisoformat(i["resolved_at"]) if i.get("resolved_at") else None
            breached = is_sla_breached(created, sla, i.get("status", "Reported"), resolved)
            if breached:
                overdue_tickets.append(
                    {
                        "ticket_id": i["ticket_id"],
                        "title": i["title"],
                        "department": i["department"],
                        "priority": i["priority_level"],
                        "status": i["status"],
                        "sla_hours": sla,
                        "created_at": i["created_at"],
                    }
                )

        total = len(raw_list)
        override_rate = round(overrides_count / total * 100, 1) if total > 0 else 0.0

        return {
            "department_workload": dept_workload,
            "overdue_count": len(overdue_tickets),
            "overdue_tickets": overdue_tickets,
            "admin_override_count": overrides_count,
            "admin_override_rate_percent": override_rate,
            "total_issues": total,
        }
