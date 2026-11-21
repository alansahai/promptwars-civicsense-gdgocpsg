"""Administrative analytics and SLA monitoring service.

Computes operational department workload, SLA breaches, and administrative
override rates for municipal dispatch officers.
"""

from datetime import datetime
from typing import Any

from app.domain.lifecycle import is_sla_breached
from app.repositories.base import IssueRepository


def _calculate_workload(raw_list: list[dict[str, Any]]) -> tuple[dict[str, dict[str, int]], int]:
    """Calculate per-department workload counts and total admin overrides."""
    dept_workload: dict[str, dict[str, int]] = {}
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

    return dept_workload, overrides_count


def _identify_overdue_tickets(raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scan all issues and collect records that have breached their target SLA."""
    overdue_tickets: list[dict[str, Any]] = []
    for i in raw_list:
        created = datetime.fromisoformat(i["created_at"])
        sla = i.get("sla_hours", 48)
        resolved = datetime.fromisoformat(i["resolved_at"]) if i.get("resolved_at") else None
        if is_sla_breached(created, sla, i.get("status", "Reported"), resolved):
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
    return overdue_tickets


class AnalyticsService:
    """Service dedicated to municipal operations and workload analysis."""

    def __init__(self, repository: IssueRepository) -> None:
        self.repo = repository

    async def get_admin_analytics(self) -> dict[str, Any]:
        """Compute advanced operational analytics for administrative monitoring."""
        raw_list = await self.repo.get_all_raw()
        dept_workload, overrides_count = _calculate_workload(raw_list)
        overdue_tickets = _identify_overdue_tickets(raw_list)

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
