"""Orchestrator for automated civic report triage.

Combines input sanitization, multimodal Gemini assessment, deterministic
priority scoring, department routing verification, and duplicate detection.
"""

from typing import Any

from app.domain.duplicates import DuplicateMatch, find_duplicates
from app.domain.models import AIAnalysis
from app.domain.priority import PriorityAssessment, calculate_priority
from app.domain.taxonomy import (
    IssueCategory,
    get_default_department,
    is_valid_department_for_category,
)
from app.services.image_utils import validate_and_decode_image
from app.services.llm import analyze_report_with_gemini
from app.services.safety import detect_prompt_injection, sanitize_user_text


class TriageResult:
    """Full triage pipeline result encapsulating all analysis stages."""

    def __init__(
        self,
        analysis: AIAnalysis,
        priority: PriorityAssessment,
        duplicates: list[DuplicateMatch],
        final_category: str,
        final_department: str,
        injection_flag: bool = False,
    ) -> None:
        self.analysis = analysis
        self.priority = priority
        self.duplicates = duplicates
        self.final_category = final_category
        self.final_department = final_department
        self.injection_flag = injection_flag


def _process_photo(photo_data_url: str | None) -> tuple[bytes | None, str | None]:
    """Decode and validate attached photo data URL."""
    if not photo_data_url:
        return None, None
    is_valid, detected_mime, raw_bytes = validate_and_decode_image(photo_data_url)
    return (raw_bytes, detected_mime) if is_valid else (None, None)


def _resolve_routing(analysis: AIAnalysis) -> tuple[str, str]:
    """Resolve validated municipal category and responsible department."""
    try:
        cat_enum = IssueCategory(analysis.category)
    except ValueError:
        cat_enum = IssueCategory.OTHER

    if is_valid_department_for_category(cat_enum.value, analysis.recommended_department):
        dept = analysis.recommended_department
    else:
        dept = get_default_department(cat_enum).value
    return cat_enum.value, dept


def _detect_duplicates(
    lat: float | None,
    lon: float | None,
    text: str,
    category: str,
    existing: list[dict[str, Any]] | None,
) -> list[DuplicateMatch]:
    """Run duplicate matching when historical issues are provided."""
    if not existing:
        return []
    return find_duplicates(
        candidate_lat=lat,
        candidate_lon=lon,
        candidate_text=text,
        candidate_category=category,
        existing_issues=existing,
    )


def _compute_priority(
    analysis: AIAnalysis,
    duplicates: list[DuplicateMatch],
    text: str,
) -> PriorityAssessment:
    """Derive deterministic priority score from analysis and context."""
    return calculate_priority(
        urgency=analysis.urgency,
        public_impact=analysis.public_impact,
        safety_risk=analysis.safety_risk,
        risk_factors=analysis.risk_factors,
        duplicate_count=len(duplicates),
        days_open=0,
        text_content=text,
    )


async def run_triage_pipeline(
    description: str,
    title: str | None = None,
    address: str | None = None,
    user_category: str | None = None,
    coords: tuple[float | None, float | None] = (None, None),
    photo_data_url: str | None = None,
    existing_issues: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> TriageResult:
    """Execute end-to-end civic report triage."""
    lat = kwargs.get("latitude", coords[0])
    lon = kwargs.get("longitude", coords[1])

    desc_clean = sanitize_user_text(description)
    title_clean = sanitize_user_text(title or "", max_length=150)
    has_injection, _ = detect_prompt_injection(description)
    photo_bytes, photo_mime = _process_photo(photo_data_url)

    analysis = await analyze_report_with_gemini(
        desc_clean, title_clean, address, user_category, photo_bytes, photo_mime
    )

    final_cat, final_dept = _resolve_routing(analysis)
    combined = f"{title_clean} {desc_clean}"
    duplicates = _detect_duplicates(lat, lon, combined, final_cat, existing_issues)
    priority = _compute_priority(analysis, duplicates, combined)

    return TriageResult(
        analysis, priority, duplicates, final_cat, final_dept, has_injection
    )
