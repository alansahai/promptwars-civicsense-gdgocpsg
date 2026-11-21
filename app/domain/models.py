"""Domain models for CivicResolve core entities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.priority import PriorityFactor


@dataclass
class StatusHistoryItem:
    """Record of a single status change or administrative note."""

    status: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    author: str = "System"
    note: str = ""
    is_public: bool = True


@dataclass
class AIAnalysis:
    """Structured result of automated AI triage."""

    category: str
    suggested_title: str
    summary: str
    detected_language: str
    urgency: str
    public_impact: int
    safety_risk: bool
    risk_factors: list[str]
    recommended_department: str
    confidence: float
    reasoning: str
    clarifying_questions: list[str]
    citizen_acknowledgement: str
    photo_observations: str | None
    ai_generated: bool = True
    analysis_source: str = "gemini"


@dataclass
class Issue:
    """Core civic grievance record."""

    ticket_id: str
    title: str
    description: str
    category: str
    department: str
    priority_level: str
    priority_score: int
    sla_hours: int
    status: str
    created_at: datetime
    updated_at: datetime
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    citizen_name: str | None = None
    has_photo: bool = False
    photo_key: str | None = None
    ai_analysis: AIAnalysis | None = None
    priority_breakdown: list[PriorityFactor] = field(default_factory=list)
    status_history: list[StatusHistoryItem] = field(default_factory=list)
    duplicate_of: str | None = None
    admin_override: bool = False
    admin_notes: str | None = None
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert domain issue to standard dictionary for serialization."""
        return {
            "ticket_id": self.ticket_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "department": self.department,
            "priority_level": self.priority_level,
            "priority_score": self.priority_score,
            "sla_hours": self.sla_hours,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "citizen_name": self.citizen_name,
            "has_photo": self.has_photo,
            "ai_analysis": self.ai_analysis.__dict__ if self.ai_analysis else None,
            "priority_breakdown": [f.__dict__ for f in self.priority_breakdown],
            "status_history": [
                {
                    "status": h.status,
                    "timestamp": h.timestamp.isoformat(),
                    "author": h.author,
                    "note": h.note,
                    "is_public": h.is_public,
                }
                for h in self.status_history
            ],
            "duplicate_of": self.duplicate_of,
            "admin_override": self.admin_override,
            "admin_notes": self.admin_notes,
        }
