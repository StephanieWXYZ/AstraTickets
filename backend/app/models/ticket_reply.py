from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.ticket import Ticket
from app.models.user import User, utc_now


class TicketReply(Base):
    __tablename__ = "ticket_replies"
    __table_args__ = (
        Index(
            "ix_ticket_replies_ticket_created_at",
            "ticket_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )

    ticket: Mapped[Ticket] = relationship(back_populates="replies")
    author: Mapped[User] = relationship(back_populates="ticket_replies")
