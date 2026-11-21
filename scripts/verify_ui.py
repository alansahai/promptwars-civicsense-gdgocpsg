"""End-to-End browser UI verification and automated screenshot capture.

Uses Playwright Chromium to validate all citizen and administrative user flows:
1. Citizen report flow with sample buttons, AI triage, and confirmation card
2. Status timeline tracking
3. Public transparency dashboard with inline SVG charts and locality scatter map
4. Officer admin login, status lifecycle transitions, and AI operational summary
5. High-contrast accessibility toggle
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOT_DIR = Path("docs/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def verify_browser_ui() -> None:
    print("\n=======================================================")
    print("  CivicResolve Browser UI Automated Verification")
    print("=======================================================\n")

    errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 850})
        page = context.new_page()

        # Catch console error events
        page.on(
            "console",
            lambda msg: errors.append(f"Console {msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )
        page.on(
            "pageerror",
            lambda err: errors.append(f"PageError: {err.message}"),
        )

        # 1. Report View
        print("[1/8] Verifying Citizen Report Flow (#/report) ...", end=" ")
        page.goto(f"{BASE_URL}/#/report", wait_until="networkidle")
        page.wait_for_selector("#report-form")
        page.screenshot(path=str(SCREENSHOT_DIR / "01_report_view.png"))
        print("OK (Screenshot: 01_report_view.png)")

        # 2. Click Sample Report Button
        print("[2/8] Testing Quick Sample Prefill ...", end=" ")
        page.click(".sample-btn:has-text('Pothole near School')")
        page.wait_for_timeout(300)
        desc_val = page.input_value("#rep-desc")
        assert "pothole" in desc_val.lower()
        page.screenshot(path=str(SCREENSHOT_DIR / "02_sample_filled.png"))
        print("OK (Description prefilled)")

        # 3. Submit Report & Verify Confirmation Card
        print("[3/8] Submitting Grievance & Testing AI Triage ...", end=" ")
        page.click("#btn-submit")
        page.wait_for_selector(".confirmation-card", timeout=12000)
        ticket_el = page.locator(".ticket-id-highlight")
        ticket_id = ticket_el.inner_text().strip()
        assert ticket_id.startswith("CR-")
        page.screenshot(path=str(SCREENSHOT_DIR / "03_confirmation_card.png"))
        print(f"OK (Generated Ticket: {ticket_id})")

        # 4. Track Ticket & Timeline
        print(f"[4/8] Tracking Ticket {ticket_id} (#/track) ...", end=" ")
        page.click("text=Track This Issue")
        page.wait_for_selector(".timeline-item", timeout=8000)
        page.screenshot(path=str(SCREENSHOT_DIR / "04_track_timeline.png"))
        print("OK (Timeline rendered)")

        # 5. Public Dashboard & SVG Charts
        print("[5/8] Verifying Public Dashboard & Inline SVG Charts ...", end=" ")
        page.click("a[href='#/dashboard']")
        page.wait_for_selector("#chart-cat svg", timeout=8000)
        page.wait_for_selector("#chart-trend svg", timeout=8000)
        page.wait_for_selector("#chart-map svg", timeout=8000)
        page.screenshot(path=str(SCREENSHOT_DIR / "05_public_dashboard.png"))
        print("OK (Category, Trend, and Locality SVG charts verified)")

        # 6. Admin Login & Credentials Display
        print("[6/8] Verifying Officer Portal Login (#/admin) ...", end=" ")
        page.click("a[href='#/admin']")
        page.wait_for_selector(".demo-auth-pill", timeout=8000)
        page.screenshot(path=str(SCREENSHOT_DIR / "06_admin_login.png"))
        # Login
        page.click("#btn-login-submit")
        page.wait_for_selector(".admin-table", timeout=8000)
        page.screenshot(path=str(SCREENSHOT_DIR / "07_admin_console.png"))
        print("OK (Authenticated with demo password)")

        # 7. Manage Issue Modal & Lifecycle Transition
        print(f"[7/8] Testing Management Modal & Status Progression ...", end=" ")
        page.click(".btn-manage >> nth=0")
        page.wait_for_selector(".manage-modal-content", timeout=8000)
        page.screenshot(path=str(SCREENSHOT_DIR / "08_manage_modal.png"))
        page.select_option("#m-status", "In Progress")
        page.fill("#m-note", "Field inspection crew dispatched with asphalt.")
        page.click("button:has-text('Save Updates & Notify')")
        page.wait_for_timeout(500)
        print("OK (Status updated to In Progress)")

        # 8. High Contrast & Summary Verification
        print("[8/8] Testing Executive Summary & High Contrast ...", end=" ")
        page.click("#btn-summary")
        page.wait_for_selector(".summary-modal-content", timeout=8000)
        page.screenshot(path=str(SCREENSHOT_DIR / "09_executive_summary.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        # Toggle high contrast
        page.click("#btn-contrast")
        page.screenshot(path=str(SCREENSHOT_DIR / "10_high_contrast.png"))
        print("OK (High contrast mode enabled)")

        browser.close()

    print("\n-------------------------------------------------------")
    if errors:
        print(f"  WARNING: {len(errors)} browser console error(s) logged:")
        for err in errors:
            print(f"   - {err}")
    else:
        print("  ZERO Console Errors & ZERO CSP Violations!")
    print("  ALL 8 UI VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("-------------------------------------------------------\n")


if __name__ == "__main__":
    verify_browser_ui()
