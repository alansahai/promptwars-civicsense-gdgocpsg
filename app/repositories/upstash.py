"""Upstash Redis REST API storage repository adapter.

Enables cloud persistence without heavy database drivers, using
lightweight async HTTP requests through httpx.
"""

import json
from datetime import datetime
from typing import Any

import httpx

from app.domain.models import AIAnalysis, Issue, PriorityFactor, StatusHistoryItem
from app.repositories.base import IssueRepository


def _deserialize_ai_analysis(ai_data: dict[str, Any] | None) -> AIAnalysis | None:
    """Deserialize AIAnalysis domain model from dictionary payload."""
    if not ai_data:
        return None
    return AIAnalysis(
        category=ai_data["category"],
        suggested_title=ai_data["suggested_title"],
        summary=ai_data["summary"],
        detected_language=ai_data["detected_language"],
        urgency=ai_data["urgency"],
        public_impact=ai_data["public_impact"],
        safety_risk=ai_data["safety_risk"],
        risk_factors=ai_data["risk_factors"],
        recommended_department=ai_data["recommended_department"],
        confidence=ai_data["confidence"],
        reasoning=ai_data["reasoning"],
        clarifying_questions=ai_data.get("clarifying_questions", []),
        citizen_acknowledgement=ai_data.get("citizen_acknowledgement", ""),
        photo_observations=ai_data.get("photo_observations"),
        ai_generated=ai_data.get("ai_generated", True),
        analysis_source=ai_data.get("analysis_source", "gemini"),
    )


def _deserialize_history(history_data: list[dict[str, Any]]) -> list[StatusHistoryItem]:
    """Deserialize list of StatusHistoryItem models from dictionaries."""
    return [
        StatusHistoryItem(
            status=h["status"],
            timestamp=datetime.fromisoformat(h["timestamp"]),
            author=h.get("author", "System"),
            note=h.get("note", ""),
            is_public=h.get("is_public", True),
        )
        for h in history_data
    ]


def _matches_criteria(
    i: Issue,
    status: str | None,
    category: str | None,
    priority: str | None,
    department: str | None,
    search: str | None,
) -> bool:
    """Check if issue matches all given query filters."""
    if status and i.status.lower() != status.lower():
        return False
    if category and i.category.lower() != category.lower():
        return False
    if priority and i.priority_level.lower() != priority.lower():
        return False
    if department and i.department.lower() != department.lower():
        return False
    if search:
        searchable = f"{i.ticket_id} {i.title} {i.description} {i.address or ''}".lower()
        if search.lower() not in searchable:
            return False
    return True


def _paginate_list(filtered: list[Issue], limit: int, cursor: str | None) -> tuple[list[Issue], str | None]:
    """Slice items based on cursor ticket_id and limit."""
    start_idx = 0
    if cursor:
        for idx, it in enumerate(filtered):
            if it.ticket_id == cursor:
                start_idx = idx + 1
                break
    page = filtered[start_idx : start_idx + limit]
    has_more = len(page) == limit and (start_idx + limit) < len(filtered)
    next_cursor = page[-1].ticket_id if has_more else None
    return page, next_cursor


class UpstashRedisRepository(IssueRepository):
    """Upstash Redis repository utilizing REST API endpoints."""

    def __init__(self, rest_url: str, rest_token: str) -> None:
        self.rest_url = rest_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {rest_token}"}
        self.client = httpx.AsyncClient(timeout=3.0, headers=self.headers)

    async def _execute_command(self, *command: Any) -> Any:
        """Execute a raw Redis command against the Upstash REST endpoint."""
        url = f"{self.rest_url}"
        response = await self.client.post(url, json=list(command))
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise RuntimeError(f"Upstash error: {data['error']}")
        return data.get("result")

    def _dict_to_issue(self, data: dict[str, Any]) -> Issue:
        """Helper to reconstruct Issue from dictionary."""
        factors = [
            PriorityFactor(f["factor"], f["points"], f["explanation"])
            for f in data.get("priority_breakdown", [])
        ]
        resolved = datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None
        return Issue(
            ticket_id=data["ticket_id"],
            title=data["title"],
            description=data["description"],
            category=data["category"],
            department=data["department"],
            priority_level=data["priority_level"],
            priority_score=data["priority_score"],
            sla_hours=data["sla_hours"],
            status=data["status"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            address=data.get("address"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            citizen_name=data.get("citizen_name"),
            has_photo=data.get("has_photo", False),
            ai_analysis=_deserialize_ai_analysis(data.get("ai_analysis")),
            priority_breakdown=factors,
            status_history=_deserialize_history(data.get("status_history", [])),
            duplicate_of=data.get("duplicate_of"),
            admin_override=data.get("admin_override", False),
            admin_notes=data.get("admin_notes"),
            resolved_at=resolved,
        )

    async def save_issue(self, issue: Issue) -> None:
        """Save issue serialized as JSON into Redis."""
        key = f"issue:{issue.ticket_id}"
        serialized = json.dumps(issue.to_dict())
        await self._execute_command("SET", key, serialized)
        await self._execute_command("SADD", "tickets:all", issue.ticket_id)

    async def get_issue_by_id(self, ticket_id: str) -> Issue | None:
        """Fetch issue by key and deserialize."""
        raw = await self._execute_command("GET", f"issue:{ticket_id}")
        if not raw:
            return None
        data = json.loads(raw)
        return self._dict_to_issue(data)

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
        """Retrieve, filter, and paginate issues."""
        ticket_ids = await self._execute_command("SMEMBERS", "tickets:all")
        if not ticket_ids:
            return [], None

        issues: list[Issue] = []
        for tid in ticket_ids:
            issue = await self.get_issue_by_id(tid)
            if issue:
                issues.append(issue)

        issues.sort(key=lambda x: (x.priority_score, x.created_at), reverse=True)
        filtered = [
            i for i in issues
            if _matches_criteria(i, status, category, priority, department, search)
        ]
        return _paginate_list(filtered, limit, cursor)

    async def update_issue(self, issue: Issue) -> None:
        """Update an existing issue."""
        await self.save_issue(issue)

    async def save_photo(self, ticket_id: str, photo_data_url: str) -> None:
        """Store photo in a distinct key to conserve bandwidth."""
        await self._execute_command("SET", f"photo:{ticket_id}", photo_data_url)
        issue = await self.get_issue_by_id(ticket_id)
        if issue:
            issue.has_photo = True
            await self.update_issue(issue)

    async def get_photo(self, ticket_id: str) -> str | None:
        """Fetch image by key."""
        return await self._execute_command("GET", f"photo:{ticket_id}")

    async def get_all_raw(self) -> list[dict[str, Any]]:
        """Return all issues as raw dicts."""
        ticket_ids = await self._execute_command("SMEMBERS", "tickets:all")
        if not ticket_ids:
            return []
        raw_list = []
        for tid in ticket_ids:
            raw = await self._execute_command("GET", f"issue:{tid}")
            if raw:
                raw_list.append(json.loads(raw))
        return raw_list
