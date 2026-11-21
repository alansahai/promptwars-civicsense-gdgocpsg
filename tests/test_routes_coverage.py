"""Tests for routes coverage, client IP extraction, CSP parity, and exception handlers."""

import json
from pathlib import Path

import pytest
from starlette.requests import Request
from starlette.testclient import TestClient

from app.api.deps import client_ip
from app.domain.errors import (
    AuthError,
    CivicResolveError,
    InvalidTransitionError,
    NotFoundError,
    UpstreamError,
    ValidationError,
)
from app.main import app, domain_exception_handler
from app.repositories.base import IssueRepository
from app.security_headers import CONTENT_SECURITY_POLICY


@pytest.fixture
def client() -> TestClient:
    """Fixture providing Starlette TestClient."""
    return TestClient(app)


def test_csp_header_matches_vercel_json() -> None:
    """Verify CSP in security_headers.py exactly matches vercel.json configuration."""
    vercel_path = Path(__file__).parent.parent / "vercel.json"
    with vercel_path.open(encoding="utf-8") as f:
        config = json.load(f)

    csp_header = None
    for header_rule in config.get("headers", []):
        if header_rule.get("source") == "/(.*)":
            for h in header_rule.get("headers", []):
                if h.get("key") == "Content-Security-Policy":
                    csp_header = h.get("value")
                    break

    assert csp_header is not None, "Content-Security-Policy missing in vercel.json"
    assert csp_header == CONTENT_SECURITY_POLICY, (
        f"CSP mismatch: Python={CONTENT_SECURITY_POLICY} vs Vercel={csp_header}"
    )


def test_client_ip_headers() -> None:
    """Verify IP address extraction precedence across proxy headers."""
    # 1. x-vercel-forwarded-for
    req1 = Request({
        "type": "http",
        "headers": [(b"x-vercel-forwarded-for", b"203.0.113.195, 10.0.0.1")],
    })
    assert client_ip(req1) == "203.0.113.195"

    # 2. x-forwarded-for
    req2 = Request({
        "type": "http",
        "headers": [(b"x-forwarded-for", b"198.51.100.42")],
    })
    assert client_ip(req2) == "198.51.100.42"

    # 3. direct client.host
    req3 = Request({
        "type": "http",
        "headers": [],
        "client": ("192.168.1.50", 12345),
    })
    assert client_ip(req3) == "192.168.1.50"

    # 4. fallback default
    req4 = Request({"type": "http", "headers": []})
    assert client_ip(req4) == "127.0.0.1"


def test_public_routes_filtering_and_photos(client: TestClient) -> None:
    """Verify filtering combinations and photo retrieval on public routes."""
    # List issues with query parameters
    res = client.get("/api/issues?status=Reported&category=Pothole&priority=High&limit=5")
    assert res.status_code == 200
    assert "items" in res.json()

    # Create issue with photo
    post_res = client.post("/api/issues", json={
        "description": "Garbage dump spilling on pavement near hospital",
        "photo_data_url": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
    })
    assert post_res.status_code == 201
    tid = post_res.json()["ticket_id"]

    # Fetch issue with lazy photo embedded
    get_res = client.get(f"/api/issues/{tid}")
    assert get_res.status_code == 200
    assert get_res.json().get("photo_data_url") is not None

    # Unknown issue 404
    res_404 = client.get("/api/issues/CR-2026-99999")
    assert res_404.status_code == 404

    # AI Assist endpoint
    res_assist = client.post("/api/assist", json={"partial_text": "Water gushing from underground pipe near park"})
    assert res_assist.status_code == 200
    assert "suggested_title" in res_assist.json()


def test_admin_routes_lifecycle(client: TestClient) -> None:
    """Verify admin login, reanalyze, and logout endpoints."""
    # Login
    login_res = client.post("/api/admin/login", json={"password": "civic-demo-2026"})
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}", "X-Civic-Admin": "1"}

    # Reanalyze nonexistent -> 404
    res_reanalyze_404 = client.post("/api/admin/issues/CR-2026-99999/reanalyze", headers=headers)
    assert res_reanalyze_404.status_code == 404

    # Create an issue to reanalyze
    post_res = client.post("/api/issues", json={
        "description": "Deep dangerous pothole right in front of primary school gate"
    })
    assert post_res.status_code == 201
    tid = post_res.json()["ticket_id"]

    # Reanalyze valid
    res_reanalyze = client.post(f"/api/admin/issues/{tid}/reanalyze", headers=headers)
    assert res_reanalyze.status_code == 200

    # Logout
    logout_res = client.post("/api/admin/logout", headers=headers)
    assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_base_repository_interface() -> None:
    """Verify protocol definition methods return None."""
    assert await IssueRepository.save_issue(None, None) is None  # type: ignore[arg-type]
    assert await IssueRepository.get_issue_by_id(None, "dummy") is None  # type: ignore[arg-type]
    assert await IssueRepository.list_issues(None) is None  # type: ignore[arg-type]
    assert await IssueRepository.update_issue(None, None) is None  # type: ignore[arg-type]
    assert await IssueRepository.save_photo(None, "dummy", "data") is None  # type: ignore[arg-type]
    assert await IssueRepository.get_photo(None, "dummy") is None  # type: ignore[arg-type]
    assert await IssueRepository.get_all_raw(None) is None  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_domain_exception_handler_coverage() -> None:
    """Verify domain_exception_handler maps each exception to its HTTP status code."""
    req = Request({"type": "http"})
    r1 = await domain_exception_handler(req, NotFoundError("not found"))
    assert r1.status_code == 404

    r2 = await domain_exception_handler(req, InvalidTransitionError("invalid"))
    assert r2.status_code == 400

    r3 = await domain_exception_handler(req, ValidationError("val"))
    assert r3.status_code == 422

    r4 = await domain_exception_handler(req, AuthError("auth"))
    assert r4.status_code == 401

    r5 = await domain_exception_handler(req, UpstreamError("upstream"))
    assert r5.status_code == 502

    r6 = await domain_exception_handler(req, CivicResolveError("generic"))
    assert r6.status_code == 400
