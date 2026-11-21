"""Strict Pydantic schemas and data transfer objects."""


from pydantic import BaseModel, ConfigDict, Field


class StrictBase(BaseModel):
    """Base model forbidding unexpected extra fields."""

    model_config = ConfigDict(extra="forbid")


class IssueCreateRequest(StrictBase):
    """Schema for submitting a new citizen grievance."""

    description: str = Field(..., min_length=10, max_length=4000)
    title: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, max_length=300)
    category: str | None = Field(default=None, max_length=50)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    citizen_name: str | None = Field(default=None, max_length=100)
    photo_data_url: str | None = Field(default=None, max_length=450000)


class IssueUpdateRequest(StrictBase):
    """Schema for administrative status update or override."""

    status: str = Field(..., max_length=50)
    note: str | None = Field(default=None, max_length=1000)
    category_override: str | None = Field(default=None, max_length=50)
    priority_override: str | None = Field(default=None, max_length=50)
    department_override: str | None = Field(default=None, max_length=80)
    duplicate_of: str | None = Field(default=None, max_length=50)


class AssistRequest(StrictBase):
    """Schema for requesting real-time description enhancement."""

    partial_text: str = Field(..., min_length=3, max_length=1000)


class AdminLoginRequest(StrictBase):
    """Admin credential submission schema."""

    password: str = Field(..., min_length=1, max_length=128)


class HealthResponse(StrictBase):
    """Service health and capability status."""

    status: str
    city_name: str
    ai_mode: str
    storage_mode: str
    demo_mode: bool
    version: str
