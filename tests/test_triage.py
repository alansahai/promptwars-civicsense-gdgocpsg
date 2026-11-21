"""Tests for end-to-end triage orchestrator pipeline."""

import pytest

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
