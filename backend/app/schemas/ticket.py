from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models import TicketPriority, TicketStatus

TicketTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=255),
]
TicketDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=10, max_length=10_000),
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


class TicketPage(BaseModel):
    items: list[TicketRead]
    total: int
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
