"""Tests for issue_service, stats_service, analytics_service, and llm edge cases."""

from unittest.mock import MagicMock, patch

import pytest

from app.domain.errors import InvalidTransitionError, NotFoundError
from app.domain.lifecycle import IssueStatus
from app.repositories.memory import InMemoryRepository
from app.services.analytics_service import AnalyticsService
from app.services.issue_service import IssueService
from app.services.llm import (
    analyze_report_with_gemini,
    generate_assistance,
    generate_executive_summary,
)
from app.services.stats_service import StatsService


@pytest.mark.asyncio
async def test_issue_service_not_found() -> None:
    """Verify update_issue_status raises NotFoundError on unknown ticket."""
    repo = InMemoryRepository()
    service = IssueService(repo)
    with pytest.raises(NotFoundError):
        await service.update_issue_status("CR-2026-00000", IssueStatus.IN_PROGRESS)


@pytest.mark.asyncio
async def test_issue_service_invalid_transition() -> None:
    """Verify illegal status transition raises InvalidTransitionError."""
    repo = InMemoryRepository()
    service = IssueService(repo)
    issue, _ = await service.create_issue(
        description="Pothole on 5th street causing road damage"
    )

    # First advance to In Progress, then Resolved
    await service.update_issue_status(issue.ticket_id, IssueStatus.IN_PROGRESS)
    await service.update_issue_status(issue.ticket_id, IssueStatus.RESOLVED)

    # Transitioning from Resolved directly back to Reported is not permitted
    with pytest.raises(InvalidTransitionError):
        await service.update_issue_status(
            issue.ticket_id,
            IssueStatus.REPORTED,
        )


@pytest.mark.asyncio
async def test_issue_service_overrides_and_delegation() -> None:
    """Verify administrative field overrides and stats delegation."""
    repo = InMemoryRepository()
    service = IssueService(repo)
    issue, _ = await service.create_issue(
        description="Garbage bin overflowing on sidewalk",
        category="Overflowing Garbage",
    )

    # Apply overrides
    updated = await service.update_issue_status(
        issue.ticket_id,
        IssueStatus.IN_PROGRESS,
        category_override="Illegal Dumping",
        priority_override="Critical",
        department_override="Environmental Safety",
        duplicate_of="CR-2026-00001",
    )
    assert updated.category == "Illegal Dumping"
    assert updated.priority_level == "Critical"
    assert updated.department == "Environmental Safety"
    assert updated.duplicate_of == "CR-2026-00001"
    assert updated.admin_override is True

    # Test stats delegation methods on IssueService
    public_stats = await service.get_public_stats()
    assert public_stats["total_issues"] >= 1

    admin_analytics = await service.get_admin_analytics()
    assert admin_analytics["total_issues"] >= 1


@pytest.mark.asyncio
async def test_issue_service_reanalyze() -> None:
    """Test reanalyze_issue updates issue triage data."""
    repo = InMemoryRepository()
    service = IssueService(repo)
    issue, _ = await service.create_issue(
        description="Dangerous exposed live wire sparking near school gate"
    )
    reanalyzed = await service.reanalyze_issue(issue.ticket_id)
    assert reanalyzed.ticket_id == issue.ticket_id
    assert reanalyzed.category in ["Exposed Live Wire", "Damaged Streetlight", "Other"]

    # Reanalyze nonexistent raises NotFoundError
    with pytest.raises(NotFoundError):
        await service.reanalyze_issue("CR-2026-99999")


@pytest.mark.asyncio
async def test_stats_and_analytics_services() -> None:
    """Verify stats and analytics computations across empty and seeded repos."""
    repo = InMemoryRepository()
    stats_svc = StatsService(repo)
    analytics_svc = AnalyticsService(repo)

    # Pre-seeded metrics
    empty_stats = await stats_svc.get_public_stats()
    assert empty_stats["total_issues"] == 15
    assert empty_stats["resolution_rate_percent"] >= 0.0

    empty_analytics = await analytics_svc.get_admin_analytics()
    assert empty_analytics["total_issues"] == 15
    assert empty_analytics["overdue_count"] == 0

    # Create issues
    issue_svc = IssueService(repo)
    await issue_svc.create_issue(description="Pothole in ward 3 needing repair")
    populated_stats = await stats_svc.get_public_stats()
    assert populated_stats["total_issues"] == 16


@pytest.mark.asyncio
async def test_llm_gemini_success_and_fallback() -> None:
    """Test LLM service with mocked Gemini interactions."""
    # Test fallback triage when gemini client is None / unconfigured
    with patch("app.services.llm._get_gemini_client", return_value=None):
        triage = await analyze_report_with_gemini("Municipal drinking water pipe burst flooding road")
        assert triage.category == "Water Leakage"
        assert triage.ai_generated is False
        assert triage.analysis_source == "rules"

        assist = await generate_assistance("Short desc")
        assert assist["suggested_title"] is not None

        summary = await generate_executive_summary({"total_issues": 10})
        assert "Civic Operations Summary" in summary

    # Test with mocked active Gemini client returning structured JSON
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"category":"Pothole","suggested_title":"Big pothole","summary":"Road crater","detected_language":"en","urgency":"High","public_impact":4,"safety_risk":true,"risk_factors":["Vehicle damage"],"recommended_department":"Roads & Highways","confidence":0.95,"reasoning":"Hazardous road cavity","clarifying_questions":["Which lane?"],"citizen_acknowledgement":"Noted"}'
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.llm._get_gemini_client", return_value=mock_client):
        # Multimodal with photo bytes
        result = await analyze_report_with_gemini(
            description="Big pothole on road",
            photo_bytes=b"fake-jpeg",
            photo_mime="image/jpeg",
        )
        assert result.category == "Pothole"
        assert result.confidence == 0.95
        assert result.ai_generated is True

        assist_res = await generate_assistance("Longer description of water pipeline leak")
        assert "suggested_title" in assist_res

        summary_res = await generate_executive_summary({"total_issues": 5, "city_name": "TestCity"})
        assert "Big pothole" in summary_res or len(summary_res) > 10
