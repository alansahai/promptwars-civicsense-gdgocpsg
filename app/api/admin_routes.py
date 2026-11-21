"""Administrative management and decision support endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import (
    get_analytics_service,
    get_auth_service,
    get_issue_service,
    get_stats_service,
    rate_limit_login,
    require_admin_auth,
)
from app.config import Settings, get_settings
from app.schemas import AdminLoginRequest, IssueUpdateRequest
from app.services.analytics_service import AnalyticsService
from app.services.auth import AuthService
from app.services.issue_service import IssueService
from app.services.llm import generate_executive_summary
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login", dependencies=[Depends(rate_limit_login)])
async def admin_login(
    payload: AdminLoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """Authenticate administrator, issue HMAC cookie, and return bearer token."""
    if not auth_service.verify_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect administrator password",
        )

    token = auth_service.create_session_token("admin")
    response.set_cookie(
        key="civic_session",
        value=token,
        max_age=8 * 3600,
        httponly=True,
        samesite="strict",
        secure=settings.is_production,
    )
    return {
        "status": "authenticated",
        "token": token,
        "message": "Admin session established successfully",
    }


@router.post("/logout")
async def admin_logout(response: Response) -> dict[str, str]:
    """Revoke admin session and clear credentials cookie."""
    response.delete_cookie(
        key="civic_session",
        httponly=True,
        samesite="strict",
    )
    return {"status": "logged_out"}


@router.get("/issues", dependencies=[Depends(require_admin_auth)])
async def list_admin_issues(
    issue_service: Annotated[IssueService, Depends(get_issue_service)],
) -> list[dict[str, Any]]:
    """Retrieve all civic issues sorted by priority score then age."""
    items, _ = await issue_service.list_issues(limit=100)
    return [it.to_dict() for it in items]


@router.patch("/issues/{ticket_id}", dependencies=[Depends(require_admin_auth)])
async def update_issue_details(
    ticket_id: str,
    payload: IssueUpdateRequest,
    issue_service: Annotated[IssueService, Depends(get_issue_service)],
) -> dict[str, Any]:
    """Update issue status or apply administrative classification overrides."""
    updated = await issue_service.update_issue_status(
        ticket_id=ticket_id,
        new_status=payload.status,
        author="Admin Officer",
        note=payload.note or "",
        category_override=payload.category_override,
        priority_override=payload.priority_override,
        department_override=payload.department_override,
        duplicate_of=payload.duplicate_of,
    )
    return updated.to_dict()


@router.post("/issues/{ticket_id}/reanalyze", dependencies=[Depends(require_admin_auth)])
async def reanalyze_issue(
    ticket_id: str,
    issue_service: Annotated[IssueService, Depends(get_issue_service)],
) -> dict[str, Any]:
    """Re-execute automated triage on an existing grievance."""
    reanalyzed = await issue_service.reanalyze_issue(ticket_id)
    return reanalyzed.to_dict()


@router.get("/analytics", dependencies=[Depends(require_admin_auth)])
async def get_admin_analytics_endpoint(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict[str, Any]:
    """Retrieve administrative analytics including department workloads and overdue SLAs."""
    return await analytics_service.get_admin_analytics()


@router.post("/summary", dependencies=[Depends(require_admin_auth)])
async def create_executive_summary(
    stats_service: Annotated[StatsService, Depends(get_stats_service)],
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> dict[str, Any]:
    """Generate Gemini executive summary grounded in operational statistics."""
    stats = await stats_service.get_public_stats()
    analytics = await analytics_service.get_admin_analytics()
    combined = {**stats, **analytics}

    summary = await generate_executive_summary(combined)
    return {
        "summary": summary,
        "generated_at": stats.get("city_name"),
    }
