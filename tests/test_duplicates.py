"""Tests for geospatial and textual duplicate detection."""


from app.domain.duplicates import (
    find_duplicates,
    haversine_distance_meters,
    text_jaccard_similarity,
)


def test_haversine_distance_accuracy():
    """Verify distance calculation between known Coimbatore GPS coordinates."""
    # RS Puram (11.0086, 76.9520) to Gandhipuram (11.0183, 76.9644) ~ 1.7 km
    dist = haversine_distance_meters(11.0086, 76.9520, 11.0183, 76.9644)
    assert 1500 < dist < 2000

    # Same location should be zero distance
    assert haversine_distance_meters(11.0, 76.0, 11.0, 76.0) == 0.0


def test_text_jaccard_similarity():
    """Verify semantic token overlap calculation."""
    text1 = "Deep pothole near government high school entrance gate"
    text2 = "Dangerous pothole near the school gate entrance"
    sim = text_jaccard_similarity(text1, text2)
    assert sim >= 0.40

    text3 = "Stray dogs barking in IT park corridor"
    sim_unrelated = text_jaccard_similarity(text1, text3)
    assert sim_unrelated == 0.0


def test_find_duplicates_matching():
    """Verify duplicate detection combines proximity and text match."""
    existing = [
        {
            "ticket_id": "CR-2026-00001",
            "title": "Water pipe leak near Alagesan Road",
            "description": "Clean water gushing from pipeline onto road",
            "category": "Water Leakage",
            "latitude": 11.0289,
            "longitude": 76.9458,
            "status": "In Progress",
        },
        {
            "ticket_id": "CR-2026-00002",
            "title": "Broken streetlight in Singanallur",
            "description": "Dark stretch of lights",
            "category": "Damaged Streetlight",
            "latitude": 10.9992,
            "longitude": 77.0256,
            "status": "Reported",
        },
    ]

    # Report close by with similar text
    dups = find_duplicates(
        candidate_lat=11.0290,
        candidate_lon=76.9460,
        candidate_text="Water pipeline burst clean water leaking on road",
        candidate_category="Water Leakage",
        existing_issues=existing,
    )

    assert len(dups) == 1
    assert dups[0].ticket_id == "CR-2026-00001"
    assert dups[0].distance_meters < 50


def test_find_duplicates_ignores_resolved():
    """Resolved issues should not be flagged as active duplicates."""
    existing = [
        {
            "ticket_id": "CR-2026-00099",
            "title": "Water pipe leak",
            "description": "Water leaking",
            "category": "Water Leakage",
            "latitude": 11.0289,
            "longitude": 76.9458,
            "status": "Resolved",
        }
    ]

    dups = find_duplicates(
        candidate_lat=11.0289,
        candidate_lon=76.9458,
        candidate_text="Water leaking",
        candidate_category="Water Leakage",
        existing_issues=existing,
    )
    assert len(dups) == 0
