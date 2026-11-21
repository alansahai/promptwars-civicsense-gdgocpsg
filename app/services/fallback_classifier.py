"""Multilingual heuristic fallback classifier.

Provides deterministic issue triage when the Gemini API is unreachable,
timed out, or unconfigured, supporting English, Tamil, and Hindi keywords.
"""

from typing import Final

from app.domain.models import AIAnalysis
from app.domain.taxonomy import IssueCategory, get_default_department

# Multilingual keyword taxonomy for category classification
KEYWORD_RULES: Final[dict[IssueCategory, list[str]]] = {
    IssueCategory.EXPOSED_WIRE: [
        "wire", "spark", "electric", "shock", "dangling", "line broken", "voltage",
        "கம்பி", "மின்சாரம்", "தீப்பொறி", "மின்கம்பி",
        "तार", "बिजली", "करंट", "स्पार्क",
    ],
    IssueCategory.POTHOLE: [
        "pothole", "crater", "road broken", "asphalt", "flyover", "skid", "road dent",
        "குழி", "பள்ளம்", "சாலை", "ரோடு",
        "गड्ढा", "सड़क", "रोड", "खड्डे",
    ],
    IssueCategory.GARBAGE: [
        "garbage", "waste", "trash", "dustbin", "overflow", "stench", "litter", "spill",
        "குப்பை", "கழிவு", "துர்நாற்றம்", "தொட்டி",
        "कचरा", "कूड़ा", "डस्टबिन", "बदबू",
    ],
    IssueCategory.WATER_LEAK: [
        "water leak", "pipeline", "pipe burst", "drinking water", "gushing", "siruvani",
        "தண்ணீர்", "குழாய்", "கசிவு", "நீர்",
        "पानी", "पाइप", "लीक", "जल",
    ],
    IssueCategory.STREETLIGHT: [
        "streetlight", "light", "lamp", "dark", "sodium", "bulb", "pitch black",
        "தெருவிளக்கு", "விளக்கு", "இருட்டு",
        "स्ट्रीट लाइट", "बत्ती", "अंधेरा", "लाइट",
    ],
    IssueCategory.SEWAGE_OVERFLOW: [
        "sewage", "drain", "gutter", "drainage", "blackwater", "manhole overflow",
        "சாக்கடை", "கழிவுநீர்", "மணல்", "கால்வாய்",
        "नाली", "सीवर", "गंदा पानी", "गटर",
    ],
    IssueCategory.STRAY_ANIMALS: [
        "dog", "stray", "cow", "cattle", "bite", "barking", "monkey", "rabies",
        "நாய்", "மாடு", "விலங்கு", "தெருநாய்",
        "कुत्ता", "गाय", "आवारा", "काट",
    ],
    IssueCategory.ILLEGAL_DUMPING: [
        "dumping", "debris", "concrete", "tipping", "unauthorized dump", "rubble",
        "கொட்டுதல்", "கட்டிட கழிவு",
        "मलबा", "डंपिंग", "अवैध",
    ],
    IssueCategory.NOISE: [
        "noise", "loudspeaker", "generator", "decibel", "sound", "volume",
        "சத்தம்", "ஒலி", "இரைச்சல்",
        "शोर", "लाउडस्पीकर", "आवाज",
    ],
}


def classify_text_heuristically(text: str) -> tuple[IssueCategory, float]:
    """Score text against category keywords and return highest match."""
    normalized = text.lower()
    scores: dict[IssueCategory, int] = dict.fromkeys(IssueCategory, 0)

    for cat, keywords in KEYWORD_RULES.items():
        for kw in keywords:
            if kw.lower() in normalized:
                scores[cat] += 1

    top_cat = max(scores, key=lambda c: scores[c])
    score_val = scores[top_cat]
    if score_val == 0:
        return IssueCategory.OTHER, 0.40

    confidence = min(0.90, 0.50 + (score_val * 0.15))
    return top_cat, confidence


def _resolve_category(user_category: str | None, text: str) -> tuple[IssueCategory, float]:
    """Resolve category from citizen selection or heuristic scan."""
    if user_category and user_category != "Let AI decide":
        try:
            return IssueCategory(user_category), 0.85
        except ValueError:
            return classify_text_heuristically(text)
    return classify_text_heuristically(text)


def _detect_urgency_and_safety(lower_text: str) -> tuple[str, int, bool]:
    """Determine urgency level, impact tier, and safety risk from keywords."""
    is_critical = any(
        k in lower_text
        for k in ["live wire", "spark", "burst", "bursting", "urgent", "danger", "hazard", "fire", "emergency", "மின்கம்பி", "बिजली"]
    )
    if is_critical:
        return "Critical", 4, True

    is_high = any(
        k in lower_text
        for k in ["crater", "overflow", "flooding", "blackwater", "stench", "accident", "school", "hospital", "குழி", "गड्ढा"]
    )
    if is_high:
        return "High", 3, True

    return "Medium", 2, False


def _extract_risk_factors(safety: bool, lower_text: str) -> list[str]:
    """Derive list of contextual risk tags from text."""
    factors = []
    if safety:
        factors.append("Safety hazard detected")
    if "school" in lower_text:
        factors.append("School zone proximity")
    if "main road" in lower_text or "flyover" in lower_text:
        factors.append("High transit road")
    return factors


def run_fallback_triage(
    description: str,
    title: str | None = None,
    user_category: str | None = None,
) -> AIAnalysis:
    """Produce comprehensive structured triage using deterministic rules."""
    text = f"{title or ''} {description}".strip()
    category, confidence = _resolve_category(user_category, text)

    lower_text = text.lower()
    urgency, impact, safety = _detect_urgency_and_safety(lower_text)
    department = get_default_department(category).value

    suggested_title = (
        title if (title and len(title.strip()) > 5)
        else f"{category.value} reported by citizen"
    )
    summary = (description[:190] + "...") if len(description) > 190 else description
    risk_factors = _extract_risk_factors(safety, lower_text)

    return AIAnalysis(
        category=category.value,
        suggested_title=suggested_title,
        summary=summary,
        detected_language="en",
        urgency=urgency,
        public_impact=impact,
        safety_risk=safety,
        risk_factors=risk_factors,
        recommended_department=department,
        confidence=confidence,
        reasoning=f"Heuristic rule classification categorized issue as {category.value} for {department}.",
        clarifying_questions=["Could you provide a nearby landmark or building name?"],
        citizen_acknowledgement="Your civic grievance has been recorded and scheduled for municipal inspection.",
        photo_observations=None,
        ai_generated=False,
        analysis_source="rules",
    )
