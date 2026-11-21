#!/usr/bin/env python3
"""CivicResolve End-to-End Smoke Test Script.

Validates core API pathways against a live or local deployment:
1. Health check & capabilities
2. Public statistics
3. Citizen issue submission with triage
4. Issue retrieval by ticket ID
5. Issues listing and filtering
6. Officer authentication and status progression
"""

import os
import sys

import httpx


def run_smoke_test(base_url: str) -> None:
    """Execute end-to-end integration verification."""
    base_url = base_url.rstrip("/")
    admin_password = os.getenv("ADMIN_PASSWORD", "civic-demo-2026")

    print("\n=======================================================")
    print(f"  CivicResolve Smoke Test Suite: {base_url}")
    print("=======================================================\n")

    client = httpx.Client(base_url=base_url, timeout=10.0)

    # 1. Health Check
    print("[1/6] Testing GET /api/health ...", end=" ")
    res = client.get("/api/health")
    if res.status_code != 200:
        print(f"FAILED ({res.status_code})")
        sys.exit(1)
    health = res.json()
    print(f"OK (City: {health['city_name']}, AI: {health['ai_mode']}, Storage: {health['storage_mode']})")

    # 2. Public Statistics
    print("[2/6] Testing GET /api/stats ...", end=" ")
    res = client.get("/api/stats")
    if res.status_code != 200:
        print(f"FAILED ({res.status_code})")
        sys.exit(1)
    stats = res.json()
    print(f"OK ({stats['total_issues']} total issues, {stats['resolution_rate_percent']}% resolved)")

    # 3. Create Sample Issue
    print("[3/6] Testing POST /api/issues ...", end=" ")
    payload = {
        "title": "Smoke test hazardous pothole",
        "description": "Deep dangerous pothole near school entrance with standing rainwater and skidding vehicles.",
        "category": "Pothole",
        "address": "DB Road near Govt School, Coimbatore",
        "latitude": 11.0086,
        "longitude": 76.9520,
        "citizen_name": "Automated Tester",
    }
    res = client.post("/api/issues", json=payload)
    if res.status_code != 201:
        print(f"FAILED ({res.status_code}: {res.text})")
        sys.exit(1)
    created = res.json()
    ticket_id = created["ticket_id"]
    print(f"OK (Ticket: {ticket_id}, Priority: {created['priority_level']} [{created['priority_score']}/100])")

    # 4. Fetch Ticket by ID
    print(f"[4/6] Testing GET /api/issues/{ticket_id} ...", end=" ")
    res = client.get(f"/api/issues/{ticket_id}")
    if res.status_code != 200:
        print(f"FAILED ({res.status_code})")
        sys.exit(1)
    fetched = res.json()
    assert fetched["ticket_id"] == ticket_id
    print(f"OK (Category: {fetched['category']}, Status: {fetched['status']})")

    # 5. List and Filter Issues
    print("[5/6] Testing GET /api/issues?limit=5 ...", end=" ")
    res = client.get("/api/issues", params={"limit": 5})
    if res.status_code != 200:
        print(f"FAILED ({res.status_code})")
        sys.exit(1)
    items = res.json()["items"]
    assert len(items) > 0
    print(f"OK ({len(items)} issues retrieved)")

    # 6. Admin Authentication & Status Transition
    print("[6/6] Testing POST /api/admin/login & PATCH status ...", end=" ")
    login_res = client.post("/api/admin/login", json={"password": admin_password})
    if login_res.status_code != 200:
        print(f"FAILED Login ({login_res.status_code}: {login_res.text})")
        sys.exit(1)
    token = login_res.json()["token"]

    admin_headers = {
        "Authorization": f"Bearer {token}",
        "X-Civic-Admin": "1",
    }

    # Transition status Reported -> In Progress
    patch_res = client.patch(
        f"/api/admin/issues/{ticket_id}",
        headers=admin_headers,
        json={
            "status": "In Progress",
            "note": "Field crew dispatched with asphalt cold patch.",
        },
    )
    if patch_res.status_code != 200:
        print(f"FAILED Transition ({patch_res.status_code}: {patch_res.text})")
        sys.exit(1)
    updated = patch_res.json()
    assert updated["status"] == "In Progress"
    print(f"OK (Ticket {ticket_id} updated to 'In Progress')")

    print("\n-------------------------------------------------------")
    print("  ALL 6 SMOKE TESTS PASSED SUCCESSFULLY! (100% HEALTHY)")
    print("-------------------------------------------------------\n")


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    run_smoke_test(target_url)
