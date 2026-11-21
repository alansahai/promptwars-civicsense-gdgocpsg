"""Tests for In-Memory repository adapter and seed dataset."""

from datetime import UTC, datetime

import pytest

from app.domain.models import Issue
from app.repositories.memory import InMemoryRepository


@pytest.mark.asyncio
async def test_memory_repo_preseeded():
    """Verify in-memory repository initializes with 15 seed issues."""
    repo = InMemoryRepository(city_name="Coimbatore")
    items, _ = await repo.list_issues(limit=100)
    assert len(items) == 15


@pytest.mark.asyncio
async def test_memory_repo_crud_and_filtering():
    """Verify CRUD and filtering by status and category."""
    repo = InMemoryRepository()

    # Filter by category
    potholes, _ = await repo.list_issues(category="Pothole")
    assert len(potholes) >= 2
    for p in potholes:
        assert p.category == "Pothole"

    # Filter by priority
    criticals, _ = await repo.list_issues(priority="Critical")
    assert len(criticals) >= 2
    for c in criticals:
        assert c.priority_level == "Critical"


@pytest.mark.asyncio
async def test_memory_repo_lazy_photo():
    """Verify photo storage is separate and lazy loaded."""
    repo = InMemoryRepository()
    tid = "CR-2026-TESTPHOTO"
    now = datetime.now(UTC)

    issue = Issue(
        ticket_id=tid,
        title="Test issue with photo",
        description="Testing photo lazy storage",
        category="Pothole",
        department="Roads & Highways",
        priority_level="Medium",
        priority_score=50,
        sla_hours=48,
        status="Reported",
        created_at=now,
        updated_at=now,
    )
    await repo.save_issue(issue)
    await repo.save_photo(tid, "data:image/jpeg;base64,TESTDATABYTES")

    fetched = await repo.get_issue_by_id(tid)
    assert fetched is not None
    assert fetched.has_photo is True

    photo = await repo.get_photo(tid)
    assert photo == "data:image/jpeg;base64,TESTDATABYTES"
