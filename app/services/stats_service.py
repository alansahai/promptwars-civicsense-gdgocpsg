"""Public grievance statistics aggregation service.

Computes municipal metrics, category counts, 14-day resolution trends,
and geospatial coordinate points for the public transparency dashboard.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import get_settings
from app.repositories.base import IssueRepository


def _compute_resolution_metrics(raw_list: list[dict[str, Any]]) -> tuple[int, int, int, float, float]:
    """Compute total, open, resolved counts, resolution rate, and average turnaround."""
    total = len(raw_list)
    resolved = sum(1 for i in raw_list if i.get("status") == "Resolved")
    open_issues = sum(1 for i in raw_list if i.get("status") in {"Reported", "In Progress"})
    rate = round((resolved / total * 100), 1) if total > 0 else 0.0

    durations: list[float] = []
    for i in raw_list:
        if i.get("status") == "Resolved" and i.get("resolved_at") and i.get("created_at"):
            c = datetime.fromisoformat(i["created_at"])
            r = datetime.fromisoformat(i["resolved_at"])
            durations.append((r - c).total_seconds() / 3600.0)

    avg_res = round(sum(durations) / len(durations), 1) if durations else 24.0
    return total, open_issues, resolved, rate, avg_res


def _compute_category_counts(raw_list: list[dict[str, Any]]) -> dict[str, int]:
    """Group issue counts by municipal category."""
    counts: dict[str, int] = {}
    for i in raw_list:
        cat = i.get("category", "Other")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _compute_14_day_trend(raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate daily volume counts for the past 14 days."""
    today = datetime.now(UTC).date()
    trend_days = [(today - timedelta(days=d)).isoformat() for d in range(13, -1, -1)]
    trend_counts = dict.fromkeys(trend_days, 0)
    for i in raw_list:
        created_str = i.get("created_at", "")[:10]
        if created_str in trend_counts:
            trend_counts[created_str] += 1
    return [{"date": d, "count": trend_counts[d]} for d in trend_days]


def _extract_map_points(raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract geographical scatter points for all mapped civic issues."""
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
    return map_points


class StatsService:
    """Service dedicated to calculating public municipal transparency metrics."""

    def __init__(self, repository: IssueRepository) -> None:
        self.repo = repository

    async def get_public_stats(self) -> dict[str, Any]:
        """Compute aggregated public statistics and dashboard metrics."""
        raw_list = await self.repo.get_all_raw()
        total, open_issues, resolved, rate, avg_res = _compute_resolution_metrics(raw_list)
        category_counts = _compute_category_counts(raw_list)
        trend = _compute_14_day_trend(raw_list)
        map_points = _extract_map_points(raw_list)

        settings = get_settings()
        return {
            "city_name": settings.city_name,
            "total_issues": total,
            "open_issues": open_issues,
            "resolved_issues": resolved,
            "resolution_rate_percent": rate,
            "average_resolution_hours": avg_res,
            "category_breakdown": category_counts,
            "trend_14_days": trend,
            "map_points": map_points,
            "storage_mode": "memory" if settings.is_in_memory_storage else "upstash",
        }
