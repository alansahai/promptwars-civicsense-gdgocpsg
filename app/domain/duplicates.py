"""Geospatial and semantic duplicate detection engine.

Pure functions for calculating geodesic distance via Haversine formula
and textual Jaccard similarity to identify duplicate civic reports.
"""

import math
import re
from dataclasses import dataclass
from typing import Any, Final

# Common English and localized stop words to filter for semantic comparison
STOP_WORDS: Final[set[str]] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "by",
    "is", "it", "this", "that", "there", "of", "from", "near", "road", "street",
    "please", "fix", "urgent", "very", "big", "here", "area", "side",
}


@dataclass(frozen=True)
class DuplicateMatch:
    """Details of an existing duplicate civic report."""

    ticket_id: str
    category: str
    distance_meters: float
    text_similarity: float
    status: str
    title: str


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two GPS coordinates in meters."""
    earth_radius_m = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_m * c


def tokenize_text(text: str) -> set[str]:
    """Tokenize and normalize text removing punctuation and stop words."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = {word for word in cleaned.split() if len(word) > 2 and word not in STOP_WORDS}
    return tokens


def text_jaccard_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard token similarity coefficient between two descriptions."""
    tokens1 = tokenize_text(text1)
    tokens2 = tokenize_text(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return float(intersection) / float(union) if union > 0 else 0.0


def find_duplicates(
    candidate_lat: float | None,
    candidate_lon: float | None,
    candidate_text: str,
    candidate_category: str,
    existing_issues: list[dict[str, Any]],
    max_distance_meters: float = 250.0,
    min_similarity: float = 0.30,
) -> list[DuplicateMatch]:
    """Identify duplicate issues based on proximity and textual similarity."""
    matches: list[DuplicateMatch] = []

    for issue in existing_issues:
        # Only check open or recently reported issues
        if issue.get("status") in {"Resolved", "Rejected"}:
            continue

        same_category = issue.get("category") == candidate_category
        other_lat = issue.get("latitude")
        other_lon = issue.get("longitude")

        distance = 0.0
        coords_match = False
        if (
            candidate_lat is not None
            and candidate_lon is not None
            and other_lat is not None
            and other_lon is not None
        ):
            distance = haversine_distance_meters(
                candidate_lat, candidate_lon, float(other_lat), float(other_lon)
            )
            coords_match = distance <= max_distance_meters

        sim = text_jaccard_similarity(
            candidate_text,
            f"{issue.get('title', '')} {issue.get('description', '')}",
        )

        # Flag as duplicate if:
        # 1. Close coordinates + same category + moderate text similarity
        # 2. Close coordinates + high text similarity
        # 3. Very high text similarity in same category even without coordinates
        is_dup = (
            (coords_match and same_category and sim >= 0.20)
            or (coords_match and sim >= 0.45)
            or (same_category and sim >= min_similarity)
        )

        if is_dup:
            matches.append(
                DuplicateMatch(
                    ticket_id=issue.get("ticket_id", ""),
                    category=issue.get("category", ""),
                    distance_meters=round(distance, 1),
                    text_similarity=round(sim, 2),
                    status=issue.get("status", "Reported"),
                    title=issue.get("title", ""),
                )
            )

    return sorted(matches, key=lambda m: (m.distance_meters, -m.text_similarity))
