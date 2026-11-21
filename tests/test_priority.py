"""Tests for pure deterministic priority scoring engine."""


from app.domain.priority import calculate_priority


def test_priority_baseline_urgency():
    """Verify urgency mapping to base points."""
    low = calculate_priority(urgency="Low", public_impact=1, safety_risk=False)
    assert low.level == "Low"
    assert low.score <= 35
    assert low.sla_hours == 72

    critical = calculate_priority(urgency="Critical", public_impact=5, safety_risk=True)
    assert critical.level == "Critical"
    assert critical.score >= 80
    assert critical.sla_hours == 8


def test_priority_safety_risk_boost():
    """Verify safety risk adds +15 points."""
    without_safety = calculate_priority(urgency="Medium", public_impact=2, safety_risk=False)
    with_safety = calculate_priority(urgency="Medium", public_impact=2, safety_risk=True)
    assert with_safety.score == without_safety.score + 15


def test_priority_risk_keywords():
    """Verify context risk keywords trigger boosts."""
    res = calculate_priority(
        urgency="Medium",
        public_impact=2,
        safety_risk=False,
        text_content="Broken wire sparking near primary school and main road",
    )
    factors = [f.factor for f in res.breakdown]
    assert any("School" in f for f in factors)
    assert any("Sparking" in f for f in factors)


def test_priority_community_duplicates_boost():
    """Verify duplicate correlation increases priority points."""
    single = calculate_priority(urgency="Low", public_impact=1, safety_risk=False, duplicate_count=0)
    with_dups = calculate_priority(urgency="Low", public_impact=1, safety_risk=False, duplicate_count=3)
    assert with_dups.score > single.score


def test_priority_aging_boost():
    """Verify unresolved aging days escalate priority points."""
    fresh = calculate_priority(urgency="Medium", public_impact=2, safety_risk=False, days_open=0)
    aged = calculate_priority(urgency="Medium", public_impact=2, safety_risk=False, days_open=4)
    assert aged.score == fresh.score + 8


def test_priority_score_clamping():
    """Ensure priority score stays bounded within [5, 100]."""
    lowest = calculate_priority(urgency="Low", public_impact=1, safety_risk=False)
    assert 5 <= lowest.score <= 100

    highest = calculate_priority(
        urgency="Critical",
        public_impact=5,
        safety_risk=True,
        text_content="live wire sparking open manhole school hospital accident drinking water sewage",
        duplicate_count=10,
        days_open=10,
    )
    assert highest.score == 100
    assert highest.level == "Critical"
