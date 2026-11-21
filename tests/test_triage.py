"""Tests for end-to-end triage orchestrator pipeline."""

import time
from unittest.mock import patch

import pytest

from app.services.llm import analyze_report_with_gemini
from app.services.triage import run_triage_pipeline


@pytest.mark.asyncio
async def test_triage_pipeline_fallback():
    """Verify full triage pipeline execution when Gemini key is not set."""
    res = await run_triage_pipeline(
        description="Sparking high voltage electrical wire dangling near primary school gate",
        title="Live wire near school",
        address="DB Road, Coimbatore",
    )

    assert res.final_category == "Exposed Live Wire"
    assert res.final_department == "Electricity & Street Lighting"
    assert res.priority.level in {"High", "Critical"}
    assert res.priority.score >= 60
    assert len(res.priority.breakdown) >= 2


@pytest.mark.asyncio
async def test_triage_department_routing_consistency():
    """Verify department routing enforces taxonomy mapping."""
    res = await run_triage_pipeline(
        description="Water main line burst gushing water onto road",
        user_category="Water Leakage",
    )

    assert res.final_department == "Water Supply & Drainage"
    assert res.priority.sla_hours <= 24


@pytest.mark.asyncio
async def test_triage_hanging_gemini_falls_back_within_budget():
    """Verify that a hanging Gemini call terminates at budget deadline and falls back to rules."""
    def hanging_generate(*_args, **_kwargs):
        time.sleep(5.0)
        return '{"category": "Other"}'

    # Simulate hanging Gemini call with a tight 0.3s test budget
    with (
        patch("app.services.llm._get_gemini_client", return_value=True),
        patch("app.services.llm.GEMINI_TOTAL_BUDGET_SECONDS", 0.3),
        patch("app.services.llm._generate_with_retry", side_effect=hanging_generate),
    ):
        start = time.monotonic()
        analysis = await analyze_report_with_gemini(
            description="Deep dangerous pothole on 100 feet road near bus stop",
            title="Dangerous pothole",
        )
        elapsed = time.monotonic() - start

        # Assert completed within budget, not hanging for 5.0 seconds
        assert elapsed < 1.0, f"Call hung for {elapsed:.2f}s instead of respecting budget"
        assert analysis.ai_generated is False
        assert analysis.analysis_source == "rules"
        assert analysis.category == "Pothole"
