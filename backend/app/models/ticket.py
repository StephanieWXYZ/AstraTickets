from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User, utc_now

if TYPE_CHECKING:
    from app.models.ticket_reply import TicketReply


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(
        SqlEnum(
            TicketStatus,
            native_enum=False,
            length=20,
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        default=TicketStatus.OPEN,
        index=True,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SqlEnum(
            TicketPriority,
            native_enum=False,
            length=20,
            values_callable=lambda priorities: [
                priority.value for priority in priorities
            ],
        ),
        default=TicketPriority.MEDIUM,
        index=True,
    )
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    requester: Mapped[User] = relationship(
        back_populates="requested_tickets",
        foreign_keys=[requester_id],
    )
    assignee: Mapped[User | None] = relationship(
        back_populates="assigned_tickets",
        foreign_keys=[assignee_id],
    )
    replies: Mapped[list["TicketReply"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketReply.created_at, TicketReply.id",
    )
