"""Tests for Upstash Redis REST repository adapter using respx."""

import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.domain.models import AIAnalysis, Issue, PriorityFactor, StatusHistoryItem
from app.repositories.upstash import (
    UpstashRedisRepository,
    _deserialize_ai_analysis,
    _deserialize_history,
    _matches_criteria,
    _paginate_list,
)


@pytest.fixture
def sample_issue() -> Issue:
    """Fixture providing a complete Issue instance."""
    now = datetime.now(UTC)
    return Issue(
        ticket_id="CR-2026-99999",
        title="Severely broken water main",
        description="Massive water leakage creating deep sinkhole",
        category="Water Leakage",
        department="Water Supply & Drainage",
        priority_level="Critical",
        priority_score=92,
        sla_hours=12,
        status="Reported",
        created_at=now,
        updated_at=now,
        address="100 Main St, Coimbatore",
        latitude=11.0123,
        longitude=76.9543,
        citizen_name="Ravi Kumar",
        has_photo=True,
        ai_analysis=AIAnalysis(
            category="Water Leakage",
            suggested_title="Water main burst",
            summary="Emergency pipeline rupture",
            detected_language="en",
            urgency="High",
            public_impact="Severe",
            safety_risk=True,
            risk_factors=["Sinkhole risk", "Drinking water loss"],
            recommended_department="Water Supply & Drainage",
            confidence=0.96,
            reasoning="High pressure burst hazard",
            clarifying_questions=["Is water entering homes?"],
            citizen_acknowledgement="Water department notified",
            photo_observations="Gushing pipe visible",
            ai_generated=True,
            analysis_source="gemini",
        ),
        priority_breakdown=[PriorityFactor("Urgency", 35, "Immediate hazard")],
        status_history=[StatusHistoryItem("Reported", now, "System", "Lodged", True)],
    )


def test_deserialize_ai_analysis_none() -> None:
    """Verify deserialization handles None gracefully."""
    assert _deserialize_ai_analysis(None) is None


def test_deserialize_history() -> None:
    """Verify status history item parsing."""
    items = _deserialize_history([
        {"status": "Reported", "timestamp": "2026-11-20T10:00:00Z", "author": "Citizen", "note": "Test", "is_public": True}
    ])
    assert len(items) == 1
    assert items[0].status == "Reported"
    assert items[0].author == "Citizen"


def test_matches_criteria_filtering(sample_issue: Issue) -> None:
    """Test filtering logic across all dimensions."""
    assert _matches_criteria(sample_issue, "Reported", "Water Leakage", "Critical", "Water Supply & Drainage", "sinkhole") is True
    assert _matches_criteria(sample_issue, "Resolved", None, None, None, None) is False
    assert _matches_criteria(sample_issue, None, "Pothole", None, None, None) is False
    assert _matches_criteria(sample_issue, None, None, "Low", None, None) is False
    assert _matches_criteria(sample_issue, None, None, None, "Roads", None) is False
    assert _matches_criteria(sample_issue, None, None, None, None, "nonexistent") is False


def test_paginate_list(sample_issue: Issue) -> None:
    """Verify pagination slicing and next_cursor generation."""
    issues = [sample_issue]
    page, cursor = _paginate_list(issues, limit=10, cursor=None)
    assert len(page) == 1
    assert cursor is None

    # Test with multiple items and limit
    now = datetime.now(UTC)
    issue2 = Issue(
        ticket_id="CR-2026-99998",
        title="Second issue",
        description="Desc",
        category="Pothole",
        department="Roads & Highways",
        priority_level="Low",
        priority_score=20,
        sla_hours=72,
        status="Reported",
        created_at=now,
        updated_at=now,
    )
    page, cursor = _paginate_list([sample_issue, issue2], limit=1, cursor=None)
    assert len(page) == 1
    assert cursor == "CR-2026-99999"

    page_next, cursor_next = _paginate_list([sample_issue, issue2], limit=1, cursor="CR-2026-99999")
    assert len(page_next) == 1
    assert page_next[0].ticket_id == "CR-2026-99998"
    assert cursor_next is None


@pytest.mark.asyncio
async def test_upstash_save_and_get(sample_issue: Issue) -> None:
    """Test saving and retrieving an issue via Upstash mock."""
    repo = UpstashRedisRepository("https://test-redis.upstash.io", "mock-token")

    with respx.mock:
        # Mock SET and SADD
        respx.post("https://test-redis.upstash.io").mock(
            return_value=httpx.Response(200, json={"result": "OK"})
        )
        await repo.save_issue(sample_issue)

        # Mock GET returning the serialized issue
        serialized = json.dumps(sample_issue.to_dict())
        respx.post("https://test-redis.upstash.io").mock(
            return_value=httpx.Response(200, json={"result": serialized})
        )
        fetched = await repo.get_issue_by_id(sample_issue.ticket_id)
        assert fetched is not None
        assert fetched.ticket_id == sample_issue.ticket_id
        assert fetched.title == sample_issue.title
        assert fetched.ai_analysis is not None
        assert fetched.ai_analysis.urgency == "High"


@pytest.mark.asyncio
async def test_upstash_get_not_found() -> None:
    """Test retrieving nonexistent issue returns None."""
    repo = UpstashRedisRepository("https://test-redis.upstash.io", "mock-token")
    with respx.mock:
        respx.post("https://test-redis.upstash.io").mock(
            return_value=httpx.Response(200, json={"result": None})
        )
        fetched = await repo.get_issue_by_id("CR-2026-00000")
        assert fetched is None


@pytest.mark.asyncio
async def test_upstash_list_issues_and_raw(sample_issue: Issue) -> None:
    """Test listing issues, filtering, and get_all_raw."""
    repo = UpstashRedisRepository("https://test-redis.upstash.io", "mock-token")
    serialized = json.dumps(sample_issue.to_dict())

    with respx.mock:
        # 1. Test empty set
        respx.post("https://test-redis.upstash.io").mock(
            return_value=httpx.Response(200, json={"result": []})
        )
        items, cursor = await repo.list_issues()
        assert items == []
        assert cursor is None

        raw = await repo.get_all_raw()
        assert raw == []

        # 2. Test populated set
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            payload = json.loads(request.content)
            cmd = payload[0]
            if cmd == "SMEMBERS":
                return httpx.Response(200, json={"result": [sample_issue.ticket_id]})
            if cmd == "GET":
                return httpx.Response(200, json={"result": serialized})
            return httpx.Response(200, json={"result": "OK"})

        respx.post("https://test-redis.upstash.io").mock(side_effect=side_effect)

        listed, cur = await repo.list_issues(status="Reported")
        assert len(listed) == 1
        assert listed[0].ticket_id == sample_issue.ticket_id

        raw_items = await repo.get_all_raw()
        assert len(raw_items) == 1
        assert raw_items[0]["ticket_id"] == sample_issue.ticket_id


@pytest.mark.asyncio
async def test_upstash_photo_operations(sample_issue: Issue) -> None:
    """Test saving and getting photo in separate redis key."""
    repo = UpstashRedisRepository("https://test-redis.upstash.io", "mock-token")
    serialized = json.dumps(sample_issue.to_dict())

    with respx.mock:
        def side_effect(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            cmd = payload[0]
            if cmd == "GET" and payload[1].startswith("photo:"):
                return httpx.Response(200, json={"result": "data:image/jpeg;base64,mock"})
            if cmd == "GET" and payload[1].startswith("issue:"):
                return httpx.Response(200, json={"result": serialized})
            return httpx.Response(200, json={"result": "OK"})

        respx.post("https://test-redis.upstash.io").mock(side_effect=side_effect)

        await repo.save_photo(sample_issue.ticket_id, "data:image/jpeg;base64,mock")
        photo = await repo.get_photo(sample_issue.ticket_id)
        assert photo == "data:image/jpeg;base64,mock"


@pytest.mark.asyncio
async def test_upstash_error_handling() -> None:
    """Test Upstash command failure raises RuntimeError."""
    repo = UpstashRedisRepository("https://test-redis.upstash.io", "mock-token")
    with respx.mock:
        respx.post("https://test-redis.upstash.io").mock(
            return_value=httpx.Response(200, json={"error": "Unauthorized quota exceeded"})
        )
        with pytest.raises(RuntimeError, match="Upstash error: Unauthorized quota exceeded"):
            await repo.get_issue_by_id("CR-2026-11111")
