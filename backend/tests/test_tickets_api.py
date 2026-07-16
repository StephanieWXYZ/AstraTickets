from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token, hash_password
from app.models import Ticket, TicketPriority, User, UserRole


def register_and_login(
    client: TestClient,
    email: str = "customer@example.com",
) -> str:
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "strong-password",
            "full_name": "Astra Customer",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        data={"username": email, "password": "strong-password"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def create_ticket(client: TestClient, token: str, title: str) -> dict[str, object]:
    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "description": "I need help resolving this support request.",
            "priority": "high",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_staff_token(
    session_factory: sessionmaker[Session],
    role: UserRole = UserRole.AGENT,
) -> str:
    with session_factory() as session:
        staff = User(
            email=f"{role.value}@example.com",
            password_hash=hash_password("strong-password"),
            full_name=f"Astra {role.value.title()}",
            role=role,
        )
        session.add(staff)
        session.commit()
        session.refresh(staff)
        return create_access_token(staff.id)


def test_customer_creates_ticket(client: TestClient) -> None:
    token = register_and_login(client)

    ticket = create_ticket(client, token, "Cannot access account")

    assert ticket["status"] == "open"
    assert ticket["priority"] == "high"
    assert ticket["assignee_id"] is None


def test_ticket_creation_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/tickets",
        json={
            "title": "Cannot access account",
            "description": "I need help resolving this support request.",
        },
    )

    assert response.status_code == 401


def test_staff_cannot_create_customer_ticket(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    token = create_staff_token(session_factory)

    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Staff-created ticket",
            "description": "This route is reserved for customer requests.",
        },
    )

    assert response.status_code == 403


def test_customer_lists_only_own_tickets(client: TestClient) -> None:
    first_token = register_and_login(client, "first@example.com")
    second_token = register_and_login(client, "second@example.com")
    create_ticket(client, first_token, "First customer ticket")
    create_ticket(client, second_token, "Second customer ticket")

    response = client.get(
        "/api/tickets",
        headers={"Authorization": f"Bearer {first_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "First customer ticket"


def test_agent_lists_and_filters_support_queue(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    create_ticket(client, customer_token, "High priority ticket")
    with session_factory() as session:
        session.add(
            Ticket(
                title="Low priority ticket",
                description="This support request can wait for an agent.",
                priority=TicketPriority.LOW,
                requester_id=1,
            )
        )
        session.commit()
    agent_token = create_staff_token(session_factory)

    response = client.get(
        "/api/tickets?priority=high&limit=1",
        headers={"Authorization": f"Bearer {agent_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["limit"] == 1
    assert response.json()["items"][0]["title"] == "High priority ticket"


def test_customer_reads_and_edits_own_open_ticket(client: TestClient) -> None:
    token = register_and_login(client)
    ticket = create_ticket(client, token, "Initial ticket title")

    read_response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    update_response = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Updated ticket title"},
    )

    assert read_response.status_code == 200
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated ticket title"


def test_customer_cannot_access_another_customers_ticket(
    client: TestClient,
) -> None:
    first_token = register_and_login(client, "first@example.com")
    second_token = register_and_login(client, "second@example.com")
    ticket = create_ticket(client, first_token, "Private customer ticket")

    response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert response.status_code == 404


def test_customer_cannot_change_ticket_status(client: TestClient) -> None:
    token = register_and_login(client)
    ticket = create_ticket(client, token, "Customer status request")

    response = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "resolved"},
    )

    assert response.status_code == 403


def test_agent_resolves_ticket_and_sets_resolution_time(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Resolve this ticket")
    agent_token = create_staff_token(session_factory)

    response = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"status": "resolved", "category": "account_access"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
    assert response.json()["category"] == "account_access"
    assert response.json()["resolved_at"] is not None


def test_closed_ticket_must_be_reopened_before_active_work(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Closed workflow ticket")
    agent_token = create_staff_token(session_factory)
    close_response = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"status": "closed"},
    )
    assert close_response.status_code == 200

    response = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"status": "in_progress"},
    )

    assert response.status_code == 409


def test_customer_deletes_unassigned_open_ticket(client: TestClient) -> None:
    token = register_and_login(client)
    ticket = create_ticket(client, token, "Delete this ticket")

    delete_response = client.delete(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    read_response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204
    assert read_response.status_code == 404


def test_agent_cannot_delete_ticket(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Permanent support record")
    agent_token = create_staff_token(session_factory)

    response = client.delete(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
    )

    assert response.status_code == 403


def test_admin_deletes_ticket(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Administrator cleanup")
    admin_token = create_staff_token(session_factory, UserRole.ADMIN)

    response = client.delete(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204
