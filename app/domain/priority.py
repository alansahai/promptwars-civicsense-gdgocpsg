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


def _score_urgency(urgency: str) -> tuple[int, str]:
    """Map LLM urgency assessment to baseline points."""
    normalized = urgency.strip().capitalize()
    mapping = {
        "Critical": (50, "Urgent triage rating: Immediate danger/disruption"),
        "High": (35, "High triage rating: Substantial disruption"),
        "Medium": (20, "Medium triage rating: Moderate inconvenience"),
        "Low": (10, "Low triage rating: Routine maintenance"),
    }
    return mapping.get(normalized, (15, "Standard baseline triage"))


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
    breakdown: list[PriorityFactor] = []

    # 1. Baseline Urgency (10-50 pts)
    urgency_pts, urgency_desc = _score_urgency(urgency)
    breakdown.append(PriorityFactor("Urgency Tier", urgency_pts, urgency_desc))

    # 2. Public Impact (5-20 pts)
    clamped_impact = max(1, min(5, public_impact))
    impact_pts = clamped_impact * 4
    breakdown.append(
        PriorityFactor(
            "Public Impact",
            impact_pts,
            f"Impact scale {clamped_impact}/5 on community density",
        )
    )

    # 3. Direct Safety Hazard (+15 pts)
    if safety_risk:
        breakdown.append(
            PriorityFactor(
                "Safety Risk",
                15,
                "Direct safety hazard flagged by automated analysis",
            )
        )

    # 4. Contextual Risk Factor Boosts
    combined_text = f"{text_content} {' '.join(risk_factors or [])}".lower()
    boost_accumulated = 0
    for keyword, (pts, reason) in RISK_KEYWORDS.items():
        if keyword in combined_text and boost_accumulated < 25:
            added = min(pts, 25 - boost_accumulated)
            boost_accumulated += added
            breakdown.append(PriorityFactor(f"Context: {keyword.title()}", added, reason))

    # 5. Community Multiplier (Duplicate Reports Boost, max +10 pts)
    if duplicate_count > 0:
        dup_pts = min(10, duplicate_count * 3)
        breakdown.append(
            PriorityFactor(
                "Community Volume",
                dup_pts,
                f"{duplicate_count} correlated nearby report(s)",
            )
        )

    # 6. Aging Escalation (+2 pts/day, max +10 pts)
    if days_open > 0:
        age_pts = min(10, days_open * 2)
        breakdown.append(
            PriorityFactor(
                "Aging Escalation",
                age_pts,
                f"Issue unresolved for {days_open} day(s)",
            )
        )

    # Total score clamped to [5, 100]
    total_score = min(100, max(5, sum(f.points for f in breakdown)))

    # Priority Tier assignment
    if total_score >= 80:
        level = "Critical"
        sla_hours = 8
    elif total_score >= 60:
        level = "High"
        sla_hours = 24
    elif total_score >= 35:
        level = "Medium"
        sla_hours = 48
    else:
        level = "Low"
        sla_hours = 72

    return PriorityAssessment(
        score=total_score,
        level=level,
        sla_hours=sla_hours,
        breakdown=breakdown,
    )
