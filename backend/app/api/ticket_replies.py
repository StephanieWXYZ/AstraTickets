from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import CurrentUser
from app.api.tickets import get_visible_ticket
from app.db.session import get_db
from app.models import TicketReply, TicketStatus, UserRole
from app.schemas import TicketReplyCreate, TicketReplyRead

router = APIRouter(
    prefix="/tickets/{ticket_id}/replies",
    tags=["ticket replies"],
)


@router.get("", response_model=list[TicketReplyRead])
def list_ticket_replies(
    ticket_id: int,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> list[TicketReply]:
    get_visible_ticket(ticket_id, current_user, session)
    return list(
        session.scalars(
            select(TicketReply)
            .options(joinedload(TicketReply.author))
            .where(TicketReply.ticket_id == ticket_id)
            .order_by(TicketReply.created_at, TicketReply.id)
        ).all()
    )


@router.post("", response_model=TicketReplyRead, status_code=status.HTTP_201_CREATED)
def create_ticket_reply(
    ticket_id: int,
    reply_data: TicketReplyCreate,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> TicketReply:
    ticket = get_visible_ticket(ticket_id, current_user, session)
    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed tickets must be reopened before replying",
        )
    if (
        current_user.role == UserRole.AGENT
        and ticket.assignee_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agents can reply only to tickets assigned to them",
        )

    if (
        current_user.role == UserRole.CUSTOMER
        and ticket.status == TicketStatus.RESOLVED
    ):
        ticket.status = (
            TicketStatus.IN_PROGRESS
            if ticket.assignee_id is not None
            else TicketStatus.OPEN
        )
        ticket.resolved_at = None

    reply = TicketReply(
        ticket_id=ticket.id,
        author_id=current_user.id,
        content=reply_data.content,
    )
    session.add(reply)
    session.commit()
    created_reply = session.scalar(
        select(TicketReply)
        .options(joinedload(TicketReply.author))
        .where(TicketReply.id == reply.id)
    )
    assert created_reply is not None
    return created_reply
