"""Municipal taxonomy definitions and routing rules.

Defines the single source of truth for categories, departments,
SLA configurations, and routing policies.
"""

from enum import StrEnum
from typing import Final


class IssueCategory(StrEnum):
    """Recognized civic issue categories."""

    POTHOLE = "Pothole"
    GARBAGE = "Overflowing Garbage"
    STREETLIGHT = "Damaged Streetlight"
    WATER_LEAK = "Water Leakage"
    EXPOSED_WIRE = "Exposed Live Wire"
    STRAY_ANIMALS = "Stray Animals"
    ILLEGAL_DUMPING = "Illegal Dumping"
    SEWAGE_OVERFLOW = "Sewage Overflow"
    NOISE = "Noise Complaint"
    OTHER = "Other"


class Department(StrEnum):
    """Municipal departments responsible for issue resolution."""

    ROADS = "Roads & Highways"
    SOLID_WASTE = "Solid Waste Management"
    ELECTRICITY = "Electricity & Street Lighting"
    WATER_SEWAGE = "Water Supply & Drainage"
    ANIMAL_CONTROL = "Animal Control & Welfare"
    TOWN_PLANNING = "Town Planning & Enforcement"
    ENVIRONMENTAL_SAFETY = "Environmental Safety"
    GENERAL_GRIEVANCE = "General Grievance"


# Category to default responsible department mapping
CATEGORY_ROUTING: Final[dict[IssueCategory, Department]] = {
    IssueCategory.POTHOLE: Department.ROADS,
    IssueCategory.GARBAGE: Department.SOLID_WASTE,
    IssueCategory.STREETLIGHT: Department.ELECTRICITY,
    IssueCategory.WATER_LEAK: Department.WATER_SEWAGE,
    IssueCategory.EXPOSED_WIRE: Department.ELECTRICITY,
    IssueCategory.STRAY_ANIMALS: Department.ANIMAL_CONTROL,
    IssueCategory.ILLEGAL_DUMPING: Department.SOLID_WASTE,
    IssueCategory.SEWAGE_OVERFLOW: Department.WATER_SEWAGE,
    IssueCategory.NOISE: Department.ENVIRONMENTAL_SAFETY,
    IssueCategory.OTHER: Department.GENERAL_GRIEVANCE,
}

# Standard SLA matrix in hours based on (Priority, Category)
SLA_MATRIX_HOURS: Final[dict[tuple[str, str], int]] = {
    ("Critical", "Exposed Live Wire"): 4,
    ("Critical", "Sewage Overflow"): 6,
    ("Critical", "Water Leakage"): 8,
    ("Critical", "*"): 12,
    ("High", "*"): 24,
    ("Medium", "*"): 48,
    ("Low", "*"): 72,
}


def get_default_department(category: IssueCategory | str) -> Department:
    """Return the designated department for a civic category."""
    if isinstance(category, str):
        try:
            category = IssueCategory(category)
        except ValueError:
            return Department.GENERAL_GRIEVANCE
    return CATEGORY_ROUTING.get(category, Department.GENERAL_GRIEVANCE)


def get_sla_hours(priority: str, category: IssueCategory | str) -> int:
    """Compute standard resolution SLA in hours for priority and category."""
    cat_str = category.value if isinstance(category, IssueCategory) else str(category)
    return SLA_MATRIX_HOURS.get((priority, cat_str), SLA_MATRIX_HOURS.get((priority, "*"), 48))


def is_valid_department_for_category(category: str, department: str) -> bool:
    """Verify if a department is plausible for a category."""
    try:
        cat_enum = IssueCategory(category)
        dept_enum = Department(department)
    except ValueError:
        return False

    expected = CATEGORY_ROUTING.get(cat_enum)
    if dept_enum in {expected, Department.GENERAL_GRIEVANCE}:
        return True

    # Plausible cross-department assignments
    cross_routing: dict[IssueCategory, set[Department]] = {
        IssueCategory.GARBAGE: {Department.ENVIRONMENTAL_SAFETY},
        IssueCategory.ILLEGAL_DUMPING: {Department.ENVIRONMENTAL_SAFETY},
        IssueCategory.EXPOSED_WIRE: {Department.ROADS},
        IssueCategory.WATER_LEAK: {Department.ROADS},
        IssueCategory.SEWAGE_OVERFLOW: {Department.ROADS},
    }
    return dept_enum in cross_routing.get(cat_enum, set())
