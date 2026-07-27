from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.models import UserRole
from app.schemas.common import as_utc

ReplyContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5_000),
]


class TicketReplyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: ReplyContent


class TicketReplyAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    role: UserRole


class TicketReplyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_id: int
    content: str
    created_at: datetime
    author: TicketReplyAuthor

    @field_validator("created_at", mode="before")
    @classmethod
    def mark_timestamp_as_utc(cls, value: datetime) -> datetime:
        timestamp = as_utc(value)
        if timestamp is None:
            raise ValueError("Reply timestamp is required")
        return timestamp
