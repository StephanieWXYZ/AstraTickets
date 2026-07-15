import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import create_database_engine
from app.models import Ticket, TicketPriority, TicketStatus, User, UserRole


@pytest.fixture
def session() -> Session:
    engine = create_database_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as database_session:
        yield database_session


def test_create_and_assign_ticket(session: Session) -> None:
    customer = User(
        email="customer@example.com",
        password_hash="customer-hash",
        full_name="Astra Customer",
    )
    agent = User(
        email="agent@example.com",
        password_hash="agent-hash",
        full_name="Astra Agent",
        role=UserRole.AGENT,
    )
    ticket = Ticket(
        title="Cannot access account",
        description="The sign-in page says my account is locked.",
        priority=TicketPriority.HIGH,
        requester=customer,
        assignee=agent,
    )

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    assert ticket.id is not None
    assert ticket.status is TicketStatus.OPEN
    assert ticket.priority is TicketPriority.HIGH
    assert ticket.requester is customer
    assert ticket.assignee is agent
    assert ticket in customer.requested_tickets
    assert ticket in agent.assigned_tickets


def test_ticket_can_wait_unassigned(session: Session) -> None:
    customer = User(
        email="waiting@example.com",
        password_hash="customer-hash",
        full_name="Waiting Customer",
    )
    ticket = Ticket(
        title="Refund question",
        description="When will my refund arrive?",
        requester=customer,
    )

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    assert ticket.assignee is None
    assert ticket.priority is TicketPriority.MEDIUM


def test_requester_cannot_be_deleted_while_ticket_exists(session: Session) -> None:
    customer = User(
        email="protected@example.com",
        password_hash="customer-hash",
        full_name="Protected Customer",
    )
    ticket = Ticket(
        title="Open support request",
        description="This ticket still belongs to its requester.",
        requester=customer,
    )
    session.add(ticket)
    session.commit()

    with pytest.raises(IntegrityError):
        session.execute(delete(User).where(User.id == customer.id))
        session.commit()
