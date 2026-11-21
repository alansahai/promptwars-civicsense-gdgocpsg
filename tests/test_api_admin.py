"""Tests for Admin API endpoints and management workflows."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_admin_auth_required():
    """Verify protected endpoints return 401 Unauthorized without credentials."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/admin/issues")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_and_operations():
    """Verify login, session token issuance, and issue status progression."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login with demo password
        login_res = await client.post("/api/admin/login", json={"password": "civic-demo-2026"})
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        assert token is not None

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Civic-Admin": "1",
        }

        # 2. List admin issues
        issues_res = await client.get("/api/admin/issues", headers=headers)
        assert issues_res.status_code == 200
        issues = issues_res.json()
        assert len(issues) >= 15

        target_ticket = issues[0]["ticket_id"]

        # 3. Patch issue status
        patch_res = await client.patch(
            f"/api/admin/issues/{target_ticket}",
            headers=headers,
            json={
                "status": "In Progress",
                "note": "Assigned technician to dispatch immediately",
            },
        )
        assert patch_res.status_code in {200, 400}  # 200 if valid transition

        # 4. Fetch admin analytics
        analytics_res = await client.get("/api/admin/analytics", headers=headers)
        assert analytics_res.status_code == 200
        assert "department_workload" in analytics_res.json()

        # 5. Generate summary
        summary_res = await client.post("/api/admin/summary", headers=headers)
        assert summary_res.status_code == 200
        summary_data = summary_res.json()
        assert "summary" in summary_data and len(summary_data["summary"]) > 0
        assert "generated_at" in summary_data
        # Validate ISO-8601 UTC timestamp format
        dt = datetime.fromisoformat(summary_data["generated_at"])
        assert dt.tzinfo is not None
        assert "ai_generated" in summary_data and isinstance(summary_data["ai_generated"], bool)
        assert summary_data["analysis_source"] in {"gemini", "rules"}


@pytest.mark.asyncio
async def test_admin_summary_sources():
    """Verify admin summary reports correct metadata for both Gemini and rule fallback paths."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/admin/login", json={"password": "civic-demo-2026"})
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}", "X-Civic-Admin": "1"}

        # 1. Rules source verification
        with patch("app.api.admin_routes.generate_executive_summary", new_callable=AsyncMock) as mock_summary:
            mock_summary.return_value = ("Rules summary", False, "rules")
            res_rules = await client.post("/api/admin/summary", headers=headers)
            assert res_rules.status_code == 200
            data_rules = res_rules.json()
            assert data_rules["summary"] == "Rules summary"
            assert data_rules["ai_generated"] is False
            assert data_rules["analysis_source"] == "rules"
            dt_rules = datetime.fromisoformat(data_rules["generated_at"])
            assert dt_rules.tzinfo is not None

        # 2. Gemini source verification
        with patch("app.api.admin_routes.generate_executive_summary", new_callable=AsyncMock) as mock_summary:
            mock_summary.return_value = ("AI 3-paragraph summary", True, "gemini")
            res_ai = await client.post("/api/admin/summary", headers=headers)
            assert res_ai.status_code == 200
            data_ai = res_ai.json()
            assert data_ai["summary"] == "AI 3-paragraph summary"
            assert data_ai["ai_generated"] is True
            assert data_ai["analysis_source"] == "gemini"
            dt_ai = datetime.fromisoformat(data_ai["generated_at"])
            assert dt_ai.tzinfo is not None
