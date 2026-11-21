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


async def run_triage_pipeline(
    description: str,
    title: str | None = None,
    address: str | None = None,
    user_category: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    photo_data_url: str | None = None,
    existing_issues: list[dict[str, Any]] | None = None,
) -> TriageResult:
    """Execute end-to-end civic report triage."""
    # 1. Text safety & sanitization
    sanitized_desc = sanitize_user_text(description)
    sanitized_title = sanitize_user_text(title or "", max_length=150)
    has_injection, _ = detect_prompt_injection(description)

    # 2. Image decoding & validation
    photo_bytes: bytes | None = None
    photo_mime: str | None = None
    if photo_data_url:
        is_valid, detected_mime, raw_bytes = validate_and_decode_image(photo_data_url)
        if is_valid:
            photo_bytes = raw_bytes
            photo_mime = detected_mime

    # 3. AI / Heuristic Triage
    ai_analysis = await analyze_report_with_gemini(
        description=sanitized_desc,
        title=sanitized_title,
        address=address,
        user_category=user_category,
        photo_bytes=photo_bytes,
        photo_mime=photo_mime,
    )

    # 4. Taxonomy & Department Verification
    try:
        final_cat_enum = IssueCategory(ai_analysis.category)
    except ValueError:
        final_cat_enum = IssueCategory.OTHER

    # Verify department routing
    if is_valid_department_for_category(final_cat_enum.value, ai_analysis.recommended_department):
        final_dept = ai_analysis.recommended_department
    else:
        final_dept = get_default_department(final_cat_enum).value

    # 5. Duplicate Detection
    duplicates = []
    if existing_issues:
        duplicates = find_duplicates(
            candidate_lat=latitude,
            candidate_lon=longitude,
            candidate_text=f"{sanitized_title} {sanitized_desc}",
            candidate_category=final_cat_enum.value,
            existing_issues=existing_issues,
        )

    # 6. Deterministic Priority Blend
    priority = calculate_priority(
        urgency=ai_analysis.urgency,
        public_impact=ai_analysis.public_impact,
        safety_risk=ai_analysis.safety_risk,
        risk_factors=ai_analysis.risk_factors,
        duplicate_count=len(duplicates),
        days_open=0,
        text_content=f"{sanitized_title} {sanitized_desc}",
    )

    return TriageResult(
        analysis=ai_analysis,
        priority=priority,
        duplicates=duplicates,
        final_category=final_cat_enum.value,
        final_department=final_dept,
        injection_flag=has_injection,
    )
