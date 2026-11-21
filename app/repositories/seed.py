"""Deterministic seed dataset generator for municipal issues.

Instantiates Issue domain models from declarative SeedSpec specifications.
"""

from datetime import UTC, datetime, timedelta

from app.domain.models import AIAnalysis, Issue, PriorityFactor, StatusHistoryItem
from app.repositories.seed_data import COIMBATORE_COORDINATES, SEED_SPECS, SeedSpec


def _build_status_history(
    spec: SeedSpec,
    created: datetime,
    resolved: datetime | None,
) -> list[StatusHistoryItem]:
    """Build chronological audit log for seed issue."""
    history = [StatusHistoryItem("Reported", created, "Citizen", "Report submitted via web portal")]
    if spec.status in {"In Progress", "Resolved", "Duplicate"}:
        note = f"Assigned to field technician ({spec.department})"
        history.append(StatusHistoryItem("In Progress", created + timedelta(hours=1), "Officer", note))
    if spec.status == "Resolved" and resolved:
        history.append(StatusHistoryItem("Resolved", resolved, "Superintendent", "Field work completed."))
    elif spec.status == "Duplicate":
        note = f"Merged with primary ticket {spec.duplicate_of}"
        history.append(StatusHistoryItem("Duplicate", created + timedelta(minutes=45), "Triage", note))
    return history


def _build_seed_analysis(spec: SeedSpec, factors: list[PriorityFactor]) -> AIAnalysis:
    """Build AI analysis record for seed issue."""
    return AIAnalysis(
        category=spec.category,
        suggested_title=spec.title,
        summary=spec.description[:180],
        detected_language="en",
        urgency=spec.urgency,
        public_impact=spec.impact,
        safety_risk=spec.safety_risk,
        risk_factors=[f.factor for f in factors],
        recommended_department=spec.department,
        confidence=0.94,
        reasoning=f"Identified as {spec.category} for {spec.department}.",
        clarifying_questions=[],
        citizen_acknowledgement="Your report has been dispatched.",
        photo_observations=None,
        ai_generated=True,
        analysis_source="gemini",
    )


def _build_single_issue(spec: SeedSpec, now: datetime, city_name: str) -> Issue:
    """Build a single domain Issue instance from SeedSpec."""
    created = now - timedelta(hours=spec.age_hours)
    resolved = now - timedelta(hours=spec.resolved_hours_ago) if spec.resolved_hours_ago else None
    coords = spec.custom_coords or COIMBATORE_COORDINATES[spec.location_key]
    factors = [PriorityFactor(f[0], f[1], f[2]) for f in spec.factors]
    return Issue(
        ticket_id=spec.ticket_id,
        title=spec.title,
        description=spec.description,
        category=spec.category,
        department=spec.department,
        priority_level=spec.priority_level,
        priority_score=spec.priority_score,
        sla_hours=spec.sla_hours,
        status=spec.status,
        created_at=created,
        updated_at=resolved or created,
        address=f"{spec.location_suffix}, {city_name}",
        latitude=coords[0],
        longitude=coords[1],
        citizen_name="Civic Citizen",
        has_photo=False,
        ai_analysis=_build_seed_analysis(spec, factors),
        priority_breakdown=factors,
        status_history=_build_status_history(spec, created, resolved),
        duplicate_of=spec.duplicate_of,
        admin_override=False,
        admin_notes=None,
        resolved_at=resolved,
    )


def generate_seed_issues(city_name: str = "Coimbatore") -> list[Issue]:
    """Generate 15 realistic seed issues across categories and statuses."""
    now = datetime.now(UTC)
    return [_build_single_issue(spec, now, city_name) for spec in SEED_SPECS]
