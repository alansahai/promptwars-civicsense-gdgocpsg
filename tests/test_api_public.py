"""Tests for Public API endpoints."""

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify GET /api/health returns operational status."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["city_name"] == "Coimbatore"
        assert "storage_mode" in data


@pytest.mark.asyncio
async def test_create_and_track_issue():
    """Verify full citizen issue submission and lookup flow."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "description": "Severe road cavity and water puddle near bus stop",
            "title": "Road cavity at bus stand",
            "address": "Gandhipuram bus stand, Coimbatore",
            "category": "Pothole",
        }
        create_res = await client.post("/api/issues", json=payload)
        assert create_res.status_code == 201
        issue_data = create_res.json()
        assert issue_data["ticket_id"].startswith("CR-")
        assert issue_data["category"] == "Pothole"
        assert issue_data["department"] == "Roads & Highways"
        assert "priority_breakdown" in issue_data

        ticket_id = issue_data["ticket_id"]

        # Track the issue
        track_res = await client.get(f"/api/issues/{ticket_id}")
        assert track_res.status_code == 200
        assert track_res.json()["ticket_id"] == ticket_id


@pytest.mark.asyncio
async def test_get_public_stats():
    """Verify GET /api/stats returns counts and chart structures."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["total_issues"] >= 15
        assert "category_breakdown" in data
        assert "trend_14_days" in data
        assert "map_points" in data


@pytest.mark.asyncio
async def test_get_description_assist():
    """Verify POST /api/assist generates title and questions."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/assist", json={"partial_text": "large pothole road broke"})
        assert res.status_code == 200
        data = res.json()
        assert "suggested_title" in data
        assert "clarifying_questions" in data
