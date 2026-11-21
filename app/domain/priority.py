"""Pure deterministic priority calculation engine.

Blends LLM urgency and impact scores with rule-based safety boosts
and contextual risk factors into an explainable 0-100 score.
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class PriorityFactor:
    """Breakdown entry explaining a component of the priority score."""

    factor: str
    points: int
    explanation: str


@dataclass(frozen=True)
class PriorityAssessment:
    """Complete priority score calculation result."""

    score: int
    level: str  # "Low" | "Medium" | "High" | "Critical"
    sla_hours: int
    breakdown: list[PriorityFactor]


# Scoring weight constraints and thresholds
MAX_CONTEXT_BOOST: Final[int] = 25
SAFETY_RISK_BOOST: Final[int] = 15
MAX_COMMUNITY_BOOST: Final[int] = 10
COMMUNITY_MULTIPLIER: Final[int] = 3
MAX_AGING_BOOST: Final[int] = 10
AGING_MULTIPLIER: Final[int] = 2

THRESHOLD_CRITICAL: Final[int] = 80
THRESHOLD_HIGH: Final[int] = 60
THRESHOLD_MEDIUM: Final[int] = 35

SLA_HOURS_CRITICAL: Final[int] = 8
SLA_HOURS_HIGH: Final[int] = 24
SLA_HOURS_MEDIUM: Final[int] = 48
SLA_HOURS_LOW: Final[int] = 72

# High-risk trigger keywords that guarantee immediate rule boosts
RISK_KEYWORDS: Final[dict[str, tuple[int, str]]] = {
    "live wire": (20, "Electrocution hazard"),
    "sparking": (15, "Fire/electrical danger"),
    "open manhole": (20, "Fall and severe trauma hazard"),
    "school": (12, "High-density children zone proximity"),
    "hospital": (12, "Emergency health corridor impact"),
    "main road": (10, "Major arterial transit obstruction"),
    "bus stop": (8, "Public transit commuter hotspot"),
    "drinking water": (15, "Potable water contamination risk"),
    "sewage": (12, "Biological public health hazard"),
    "accident": (15, "Direct traffic safety peril"),
}


def urgency_points(urgency: str) -> PriorityFactor:
    """Map LLM urgency assessment to a PriorityFactor."""
    normalized = urgency.strip().capitalize()
    mapping = {
        "Critical": (50, "Urgent triage rating: Immediate danger/disruption"),
        "High": (35, "High triage rating: Substantial disruption"),
        "Medium": (20, "Medium triage rating: Moderate inconvenience"),
        "Low": (10, "Low triage rating: Routine maintenance"),
    }
    pts, desc = mapping.get(normalized, (15, "Standard baseline triage"))
    return PriorityFactor("Urgency Tier", pts, desc)


def impact_points(public_impact: int) -> PriorityFactor:
    """Calculate public impact component (5-20 points)."""
    clamped = max(1, min(5, public_impact))
    return PriorityFactor("Public Impact", clamped * 4, f"Impact scale {clamped}/5 on community density")


def safety_points(safety_risk: bool) -> PriorityFactor | None:
    """Return safety risk bonus factor if safety_risk is set."""
    if not safety_risk:
        return None
    return PriorityFactor("Safety Risk", SAFETY_RISK_BOOST, "Direct safety hazard flagged by automated analysis")


def context_points(text_content: str, risk_factors: list[str] | None) -> list[PriorityFactor]:
    """Extract keyword context boosts up to MAX_CONTEXT_BOOST."""
    combined_text = f"{text_content} {' '.join(risk_factors or [])}".lower()
    factors: list[PriorityFactor] = []
    accumulated = 0
    for keyword, (pts, reason) in RISK_KEYWORDS.items():
        if keyword in combined_text and accumulated < MAX_CONTEXT_BOOST:
            added = min(pts, MAX_CONTEXT_BOOST - accumulated)
            accumulated += added
            factors.append(PriorityFactor(f"Context: {keyword.title()}", added, reason))
    return factors


def community_points(duplicate_count: int) -> PriorityFactor | None:
    """Calculate volume bonus for correlated duplicate issues."""
    if duplicate_count <= 0:
        return None
    pts = min(MAX_COMMUNITY_BOOST, duplicate_count * COMMUNITY_MULTIPLIER)
    return PriorityFactor("Community Volume", pts, f"{duplicate_count} correlated nearby report(s)")


def aging_points(days_open: int) -> PriorityFactor | None:
    """Calculate escalation factor for issues that remain open over time."""
    if days_open <= 0:
        return None
    pts = min(MAX_AGING_BOOST, days_open * AGING_MULTIPLIER)
    return PriorityFactor("Aging Escalation", pts, f"Issue unresolved for {days_open} day(s)")


def to_level_and_sla(score: int) -> tuple[str, int]:
    """Map numeric priority score to human level name and target SLA hours."""
    if score >= THRESHOLD_CRITICAL:
        return "Critical", SLA_HOURS_CRITICAL
    if score >= THRESHOLD_HIGH:
        return "High", SLA_HOURS_HIGH
    if score >= THRESHOLD_MEDIUM:
        return "Medium", SLA_HOURS_MEDIUM
    return "Low", SLA_HOURS_LOW


def calculate_priority(
    urgency: str,
    public_impact: int,
    safety_risk: bool,
    risk_factors: list[str] | None = None,
    duplicate_count: int = 0,
    days_open: int = 0,
    text_content: str = "",
) -> PriorityAssessment:
    """Calculate deterministic priority score (0-100) and explainable breakdown."""
    breakdown: list[PriorityFactor] = [
        urgency_points(urgency),
        impact_points(public_impact),
    ]

    safe_f = safety_points(safety_risk)
    if safe_f:
        breakdown.append(safe_f)

    breakdown.extend(context_points(text_content, risk_factors))

    comm_f = community_points(duplicate_count)
    if comm_f:
        breakdown.append(comm_f)

    age_f = aging_points(days_open)
    if age_f:
        breakdown.append(age_f)

    total_score = min(100, max(5, sum(f.points for f in breakdown)))
    level, sla_hours = to_level_and_sla(total_score)

    return PriorityAssessment(
        score=total_score,
        level=level,
        sla_hours=sla_hours,
        breakdown=breakdown,
    )
