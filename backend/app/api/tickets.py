from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.models import Ticket, TicketPriority, TicketStatus, UserRole
from app.schemas import TicketCreate, TicketPage, TicketRead

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Ticket:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create tickets",
        )

    ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        requester_id=current_user.id,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


@router.get("", response_model=TicketPage)
def list_tickets(
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
    ticket_status: Annotated[TicketStatus | None, Query(alias="status")] = None,
    priority: TicketPriority | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TicketPage:
    filters = []
    if current_user.role == UserRole.CUSTOMER:
        filters.append(Ticket.requester_id == current_user.id)
    if ticket_status is not None:
        filters.append(Ticket.status == ticket_status)
    if priority is not None:
        filters.append(Ticket.priority == priority)

    total = session.scalar(select(func.count(Ticket.id)).where(*filters)) or 0
    tickets = session.scalars(
        select(Ticket)
        .where(*filters)
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return TicketPage(
        items=[TicketRead.model_validate(ticket) for ticket in tickets],
        total=total,
        offset=offset,
        limit=limit,
    )
