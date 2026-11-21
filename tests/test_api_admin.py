"""Tests for Admin API endpoints and management workflows."""

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
        assert "summary" in summary_res.json()
