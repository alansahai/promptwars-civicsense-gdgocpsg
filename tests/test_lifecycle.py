"""Tests for lifecycle state machine and SLA breach tracking."""

from datetime import UTC, datetime

from app.domain.lifecycle import (
    IssueStatus,
    can_transition,
    compute_sla_due_date,
    is_sla_breached,
)


def test_lifecycle_allowed_transitions():
    """Verify valid state transitions."""
    assert can_transition(IssueStatus.REPORTED, IssueStatus.IN_PROGRESS) is True
    assert can_transition(IssueStatus.REPORTED, IssueStatus.REJECTED) is True
    assert can_transition(IssueStatus.REPORTED, IssueStatus.DUPLICATE) is True
    assert can_transition(IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED) is True
    assert can_transition(IssueStatus.RESOLVED, IssueStatus.IN_PROGRESS) is True


def test_lifecycle_disallowed_transitions():
    """Verify invalid state transitions are blocked."""
    # Cannot jump directly from Reported to Resolved without In Progress
    assert can_transition(IssueStatus.REPORTED, IssueStatus.RESOLVED) is False
    # Cannot jump from Resolved to Reported
    assert can_transition(IssueStatus.RESOLVED, IssueStatus.REPORTED) is False


def test_sla_due_date_calculation():
    """Verify SLA deadline computation."""
    created = datetime(2026, 11, 21, 10, 0, tzinfo=UTC)
    deadline = compute_sla_due_date(created, 24)
    assert deadline == datetime(2026, 11, 22, 10, 0, tzinfo=UTC)


def test_sla_breach_detection():
    """Verify breach detection on open and resolved issues."""
    created = datetime(2026, 11, 20, 10, 0, tzinfo=UTC)
    now_on_track = datetime(2026, 11, 20, 18, 0, tzinfo=UTC)
    now_breached = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)

    # 24-hour SLA
    assert is_sla_breached(created, 24, "In Progress", now=now_on_track) is False
    assert is_sla_breached(created, 24, "In Progress", now=now_breached) is True

    # Resolved within SLA
    resolved_early = datetime(2026, 11, 20, 20, 0, tzinfo=UTC)
    assert is_sla_breached(created, 24, "Resolved", resolved_at=resolved_early, now=now_breached) is False
