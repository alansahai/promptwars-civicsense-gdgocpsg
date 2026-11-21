"""Civic issue lifecycle state machine and SLA tracker.

Validates status transitions and computes SLA deadlines and breaches.
"""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Final


class IssueStatus(StrEnum):
    """Permitted states for a civic issue ticket."""

    REPORTED = "Reported"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    REJECTED = "Rejected"
    DUPLICATE = "Duplicate"


# Allowed state transitions: key -> set of legal target states
TRANSITION_GRAPH: Final[dict[IssueStatus, set[IssueStatus]]] = {
    IssueStatus.REPORTED: {
        IssueStatus.IN_PROGRESS,
        IssueStatus.REJECTED,
        IssueStatus.DUPLICATE,
    },
    IssueStatus.IN_PROGRESS: {
        IssueStatus.RESOLVED,
        IssueStatus.REJECTED,
        IssueStatus.DUPLICATE,
        IssueStatus.REPORTED,  # Admin reassignment
    },
    IssueStatus.RESOLVED: {
        IssueStatus.IN_PROGRESS,  # Reopened by admin
    },
    IssueStatus.REJECTED: {
        IssueStatus.IN_PROGRESS,  # Re-evaluated upon appeal
    },
    IssueStatus.DUPLICATE: {
        IssueStatus.IN_PROGRESS,  # Reopened if found unique
    },
}


def can_transition(current: IssueStatus | str, target: IssueStatus | str) -> bool:
    """Check if transitioning from current to target status is permitted."""
    try:
        curr_enum = IssueStatus(current)
        targ_enum = IssueStatus(target)
        if curr_enum == targ_enum:
            return True
        allowed = TRANSITION_GRAPH.get(curr_enum, set())
        return targ_enum in allowed
    except ValueError:
        return False


def compute_sla_due_date(created_at: datetime, sla_hours: int) -> datetime:
    """Calculate the absolute SLA deadline timestamp."""
    return created_at + timedelta(hours=sla_hours)


def is_sla_breached(
    created_at: datetime,
    sla_hours: int,
    status: IssueStatus | str,
    resolved_at: datetime | None = None,
    now: datetime | None = None,
) -> bool:
    """Determine whether the resolution SLA has been breached."""
    current_time = now or datetime.now(UTC)
    deadline = compute_sla_due_date(created_at, sla_hours)

    if status in {IssueStatus.RESOLVED, IssueStatus.REJECTED, IssueStatus.DUPLICATE}:
        effective_resolution = resolved_at or current_time
        return effective_resolution > deadline

    return current_time > deadline
