from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models import TicketPriority, TicketStatus

TicketTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=255),
]
TicketDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=10, max_length=10_000),
]
TicketCategory = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TicketTitle
    description: TicketDescription
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: str | None
    requester_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class TicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TicketTitle | None = None
    description: TicketDescription | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    category: TicketCategory | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "TicketUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        required_values = {"title", "description", "priority", "status"}
        for field_name in self.model_fields_set & required_values:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class TicketAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignee_id: int | None = Field(default=None, ge=1)


class TicketPage(BaseModel):
    items: list[TicketRead]
    total: int
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
