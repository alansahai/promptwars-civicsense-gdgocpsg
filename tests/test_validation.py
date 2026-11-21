"""Tests for strict Pydantic validation rules."""

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_validation_short_description_rejected():
    """Verify description under 10 chars produces 422 Unprocessable Entity."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/issues", json={"description": "short"})
        assert res.status_code == 422
        data = res.json()
        assert "errors" in data or "detail" in data


@pytest.mark.asyncio
async def test_validation_extra_fields_forbidden():
    """Verify extra unexpected fields are rejected due to extra='forbid'."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/issues",
            json={
                "description": "Valid detailed description of broken pothole on road",
                "unknown_malicious_field": "injected",
            },
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_validation_lat_lon_bounds():
    """Verify latitude and longitude out-of-bounds produce 422."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/issues",
            json={
                "description": "Valid detailed description of broken pothole on road",
                "latitude": 95.0,  # invalid lat > 90
            },
        )
        assert res.status_code == 422
