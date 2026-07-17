from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import decode_access_token
from tests.api_helpers import (
    claim_ticket,
    create_staff_token,
    create_ticket,
    register_and_login,
)


def post_reply(
    client: TestClient,
    token: str,
    ticket_id: object,
    content: str,
) -> dict[str, object]:
    response = client.post(
        f"/api/tickets/{ticket_id}/replies",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": content},
    )
    assert response.status_code == 201
    return response.json()


def test_customer_reply_uses_authenticated_author(client: TestClient) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Customer conversation")

    reply = post_reply(
        client,
        customer_token,
        ticket["id"],
        "Here are more details about the problem.",
    )

    assert reply["author_id"] == decode_access_token(customer_token)
    assert reply["author"]["role"] == "customer"
    assert reply["author"]["full_name"] == "Astra Customer"


def test_reply_rejects_client_supplied_author(client: TestClient) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Spoofed reply attempt")

    response = client.post(
        f"/api/tickets/{ticket['id']}/replies",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"content": "A valid reply body.", "author_id": 999},
    )

    assert response.status_code == 422


def test_conversation_lists_customer_and_assigned_agent_replies(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Two-way conversation")
    agent_token = create_staff_token(session_factory)
    post_reply(client, customer_token, ticket["id"], "Customer message")
    claim_ticket(client, agent_token, ticket["id"])
    post_reply(client, agent_token, ticket["id"], "Agent response")

    response = client.get(
        f"/api/tickets/{ticket['id']}/replies",
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    assert response.status_code == 200
    assert [reply["content"] for reply in response.json()] == [
        "Customer message",
        "Agent response",
    ]
    assert [reply["author"]["role"] for reply in response.json()] == [
        "customer",
        "agent",
    ]


def test_unassigned_agent_cannot_reply(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Unassigned conversation")
    agent_token = create_staff_token(session_factory)

    response = client.post(
        f"/api/tickets/{ticket['id']}/replies",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"content": "I have not claimed this ticket."},
    )

    assert response.status_code == 403


def test_customer_cannot_read_another_customers_conversation(
    client: TestClient,
) -> None:
    first_token = register_and_login(client, "first@example.com")
    second_token = register_and_login(client, "second@example.com")
    ticket = create_ticket(client, first_token, "Private conversation")
    post_reply(client, first_token, ticket["id"], "Private details")

    response = client.get(
        f"/api/tickets/{ticket['id']}/replies",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert response.status_code == 404


def test_customer_reply_reopens_resolved_ticket(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Reopened conversation")
    agent_token = create_staff_token(session_factory)
    claim_ticket(client, agent_token, ticket["id"])
    resolve_response = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"status": "resolved"},
    )
    assert resolve_response.status_code == 200

    post_reply(
        client,
        customer_token,
        ticket["id"],
        "The suggested fix did not solve the problem.",
    )
    ticket_response = client.get(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    assert ticket_response.json()["status"] == "in_progress"
    assert ticket_response.json()["resolved_at"] is None


def test_closed_ticket_rejects_replies(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    ticket = create_ticket(client, customer_token, "Closed conversation")
    agent_token = create_staff_token(session_factory)
    claim_ticket(client, agent_token, ticket["id"])
    close_response = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"status": "closed"},
    )
    assert close_response.status_code == 200

    response = client.post(
        f"/api/tickets/{ticket['id']}/replies",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"content": "This closed ticket should stay locked."},
    )

    assert response.status_code == 409
