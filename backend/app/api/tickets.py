from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.models import Ticket, TicketPriority, TicketStatus, User, UserRole
from app.schemas import (
    TicketAssignment,
    TicketCreate,
    TicketPage,
    TicketRead,
    TicketUpdate,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])

allowed_status_transitions = {
    TicketStatus.OPEN: {
        TicketStatus.IN_PROGRESS,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    },
    TicketStatus.IN_PROGRESS: {
        TicketStatus.OPEN,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    },
    TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.CLOSED: {TicketStatus.OPEN},
}


def get_visible_ticket(
    ticket_id: int,
    current_user: CurrentUser,
    session: Session,
) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None or (
        current_user.role == UserRole.CUSTOMER
        and ticket.requester_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


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


@router.get("/{ticket_id}", response_model=TicketRead)
def read_ticket(
    ticket_id: int,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Ticket:
    return get_visible_ticket(ticket_id, current_user, session)


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Ticket:
    ticket = get_visible_ticket(ticket_id, current_user, session)
    changes = ticket_data.model_dump(exclude_unset=True)

    if current_user.role == UserRole.CUSTOMER:
        customer_fields = {"title", "description", "priority"}
        if not changes.keys() <= customer_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers cannot change staff-managed fields",
            )
        if ticket.status != TicketStatus.OPEN or ticket.assignee_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assigned or active tickets cannot be edited by customers",
            )
    elif (
        current_user.role == UserRole.AGENT
        and ticket.assignee_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agents can update only tickets assigned to them",
        )

    new_status = changes.get("status")
    if new_status is not None and new_status != ticket.status:
        if new_status not in allowed_status_transitions[ticket.status]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot move ticket from {ticket.status.value} to {new_status.value}",
            )
        if (
            new_status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}
            and ticket.resolved_at is None
        ):
            ticket.resolved_at = datetime.now(timezone.utc)
        elif new_status in {TicketStatus.OPEN, TicketStatus.IN_PROGRESS}:
            ticket.resolved_at = None

    for field_name, value in changes.items():
        setattr(ticket, field_name, value)

    session.commit()
    session.refresh(ticket)
    return ticket


@router.patch("/{ticket_id}/assignment", response_model=TicketRead)
def assign_ticket(
    ticket_id: int,
    assignment: TicketAssignment,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Ticket:
    ticket = get_visible_ticket(ticket_id, current_user, session)
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot assign tickets",
        )
    if ticket.status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolved or closed tickets must be reopened before assignment",
        )

    if assignment.assignee_id is None:
        if (
            current_user.role == UserRole.AGENT
            and ticket.assignee_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agents can release only their own tickets",
            )
        ticket.assignee_id = None
        if ticket.status == TicketStatus.IN_PROGRESS:
            ticket.status = TicketStatus.OPEN
    else:
        assignee = session.get(User, assignment.assignee_id)
        if assignee is None:
            raise HTTPException(status_code=404, detail="Assignee not found")
        if not assignee.is_active or assignee.role == UserRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tickets can be assigned only to active staff",
            )
        if current_user.role == UserRole.AGENT:
            if assignment.assignee_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Agents can assign tickets only to themselves",
                )
            if ticket.assignee_id not in {None, current_user.id}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ticket is already assigned to another agent",
                )

        ticket.assignee_id = assignee.id
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS

    session.commit()
    session.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    ticket = get_visible_ticket(ticket_id, current_user, session)

    if current_user.role == UserRole.AGENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agents cannot delete tickets",
        )
    if current_user.role == UserRole.CUSTOMER and (
        ticket.status != TicketStatus.OPEN or ticket.assignee_id is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assigned or active tickets cannot be deleted by customers",
        )

    session.delete(ticket)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
