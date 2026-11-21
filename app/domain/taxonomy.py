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

# SLA in hours based on (Category, Priority Level)
# Priority levels: "Critical", "High", "Medium", "Low"
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
    try:
        cat_enum = IssueCategory(category)
        return CATEGORY_ROUTING.get(cat_enum, Department.GENERAL_GRIEVANCE)
    except ValueError:
        return Department.GENERAL_GRIEVANCE


def get_sla_hours(priority: str, category: IssueCategory | str) -> int:
    """Compute standard resolution SLA in hours for priority and category."""
    cat_str = str(category)
    if (priority, cat_str) in SLA_MATRIX_HOURS:
        return SLA_MATRIX_HOURS[(priority, cat_str)]
    return SLA_MATRIX_HOURS.get((priority, "*"), 48)


def is_valid_department_for_category(category: str, department: str) -> bool:
    """Verify if a department is plausible for a category."""
    try:
        cat_enum = IssueCategory(category)
        dept_enum = Department(department)
        expected = CATEGORY_ROUTING.get(cat_enum)
        if dept_enum == expected:
            return True
        # Cross-department plausible cases
        if cat_enum in {IssueCategory.GARBAGE, IssueCategory.ILLEGAL_DUMPING} and dept_enum in {
            Department.SOLID_WASTE,
            Department.ENVIRONMENTAL_SAFETY,
        }:
            return True
        if cat_enum == IssueCategory.EXPOSED_WIRE and dept_enum in {
            Department.ELECTRICITY,
            Department.ROADS,
        }:
            return True
        if cat_enum in {IssueCategory.WATER_LEAK, IssueCategory.SEWAGE_OVERFLOW} and dept_enum in {
            Department.WATER_SEWAGE,
            Department.ROADS,
        }:
            return True
        return dept_enum == Department.GENERAL_GRIEVANCE
    except ValueError:
        return False
