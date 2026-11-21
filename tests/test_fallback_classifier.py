"""Tests for multilingual heuristic fallback classifier."""


from app.domain.taxonomy import IssueCategory
from app.services.fallback_classifier import (
    classify_text_heuristically,
    run_fallback_triage,
)


def test_fallback_english_categories():
    """Verify keyword classification on English civic descriptions."""
    cat, conf = classify_text_heuristically("Large crater pothole on flyover descent")
    assert cat == IssueCategory.POTHOLE
    assert conf >= 0.60

    cat_wire, _ = classify_text_heuristically("High voltage electric line broken sparking")
    assert cat_wire == IssueCategory.EXPOSED_WIRE


def test_fallback_tamil_categories():
    """Verify classification on Tamil descriptions."""
    cat_garbage, _ = classify_text_heuristically("ரோட்டில் குப்பை தொட்டி நிரம்பி துர்நாற்றம் அடிக்கிறது")
    assert cat_garbage == IssueCategory.GARBAGE

    cat_water, _ = classify_text_heuristically("குடிநீர் குழாய் உடைந்து தண்ணீர் வீணாக போகிறது")
    assert cat_water == IssueCategory.WATER_LEAK


def test_fallback_hindi_categories():
    """Verify classification on Hindi descriptions."""
    cat_pothole, _ = classify_text_heuristically("सड़क पर बहुत बड़ा गड्ढा है गाड़ियां गिर रही हैं")
    assert cat_pothole == IssueCategory.POTHOLE

    cat_wire, _ = classify_text_heuristically("बिजली का नंगा तार जमीन पर गिरा हुआ है करंट लग सकता है")
    assert cat_wire == IssueCategory.EXPOSED_WIRE


def test_run_fallback_triage_structure():
    """Verify fallback triage returns fully populated AIAnalysis."""
    analysis = run_fallback_triage("Dead animals and waste piled up on road side")
    assert analysis.ai_generated is False
    assert analysis.analysis_source == "rules"
    assert len(analysis.suggested_title) > 0
    assert analysis.recommended_department is not None
    assert analysis.urgency in {"Low", "Medium", "High", "Critical"}
