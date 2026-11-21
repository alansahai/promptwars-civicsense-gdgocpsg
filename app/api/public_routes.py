"""Public API endpoints for citizens and transparency dashboards."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_issue_service, get_stats_service, rate_limit_reports
from app.config import Settings, get_settings
from app.schemas import AssistRequest, HealthResponse, IssueCreateRequest
from app.services.issue_service import IssueService
from app.services.llm import generate_assistance
from app.services.stats_service import StatsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["public"])


class IssueFilterParams:
    """Query parameter filter bundle for issue listing."""

    def __init__(
        self,
        status: str | None = Query(default=None),
        category: str | None = Query(default=None),
        priority: str | None = Query(default=None),
        department: str | None = Query(default=None),
        search: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
        cursor: str | None = Query(default=None),
    ) -> None:
        self.status = status
        self.category = category
        self.priority = priority
        self.department = department
        self.search = search
        self.limit = limit
        self.cursor = cursor


@router.get("/health", response_model=HealthResponse)
async def check_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Report operational health and system capabilities."""
    return HealthResponse(
        status="healthy",
        city_name=settings.city_name,
        ai_mode="gemini" if settings.has_gemini_key else "rules",
        storage_mode="memory" if settings.is_in_memory_storage else "upstash",
        demo_mode=settings.demo_mode,
        version="1.0.0",
    )


@router.post("/issues", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_reports)])
async def create_new_issue(
    payload: IssueCreateRequest,
    issue_service: Annotated[IssueService, Depends(get_issue_service)],
) -> dict[str, Any]:
    """Submit a citizen grievance, run automated AI triage, and return ticket confirmation."""
    if payload.latitude and payload.longitude:
        logger.info("Lodging report near lat: %.3f, lon: %.3f", payload.latitude, payload.longitude)

    issue, duplicates = await issue_service.create_issue(
        description=payload.description,
        title=payload.title,
        address=payload.address,
        category=payload.category,
        latitude=payload.latitude,
        longitude=payload.longitude,
        citizen_name=payload.citizen_name,
        photo_data_url=payload.photo_data_url,
    )

    issue_dict = issue.to_dict()
    issue_dict["duplicates"] = [
        {
            "ticket_id": d.ticket_id,
            "category": d.category,
            "distance_meters": d.distance_meters,
            "text_similarity": d.text_similarity,
            "status": d.status,
            "title": d.title,
        }
        for d in duplicates
    ]
    return issue_dict


@router.get("/issues")
async def list_public_issues(
    issue_service: Annotated[IssueService, Depends(get_issue_service)],
    filters: Annotated[IssueFilterParams, Depends()],
) -> dict[str, Any]:
    """Retrieve filtered, paginated list of civic grievances."""
    items, next_cursor = await issue_service.list_issues(
        status=filters.status,
        category=filters.category,
        priority=filters.priority,
        department=filters.department,
        search=filters.search,
        limit=filters.limit,
        cursor=filters.cursor,
    )
    return {
        "items": [it.to_dict() for it in items],
        "next_cursor": next_cursor,
    }


@router.get("/issues/{ticket_id}")
async def get_issue_by_ticket_id(
    ticket_id: str,
    issue_service: Annotated[IssueService, Depends(get_issue_service)],
) -> dict[str, Any]:
    """Retrieve full issue tracking record with timeline and lazy photo."""
    issue = await issue_service.get_issue(ticket_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    data = issue.to_dict()
    if issue.has_photo:
        photo = await issue_service.get_issue_photo(ticket_id)
        data["photo_data_url"] = photo
    return data


@router.get("/stats")
async def get_aggregated_stats(
    stats_service: Annotated[StatsService, Depends(get_stats_service)],
) -> dict[str, Any]:
    """Retrieve public transparency metrics and SVG chart data points."""
    return await stats_service.get_public_stats()


@router.post("/assist")
async def get_description_assistance(payload: AssistRequest) -> dict[str, Any]:
    """Real-time AI title suggestion and clarifying questions for citizens."""
    return await generate_assistance(payload.partial_text)
