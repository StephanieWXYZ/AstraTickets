from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token, decode_access_token, hash_password
from app.models import User, UserRole


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
    email_prefix: str | None = None,
) -> str:
    prefix = email_prefix or role.value
    with session_factory() as session:
        staff = User(
            email=f"{prefix}@example.com",
            password_hash=hash_password("strong-password"),
            full_name=f"Astra {role.value.title()}",
            role=role,
        )
        session.add(staff)
        session.commit()
        session.refresh(staff)
        return create_access_token(staff.id)


def claim_ticket(
    client: TestClient,
    token: str,
    ticket_id: object,
) -> dict[str, object]:
    response = client.patch(
        f"/api/tickets/{ticket_id}/assignment",
        headers={"Authorization": f"Bearer {token}"},
        json={"assignee_id": decode_access_token(token)},
    )
    assert response.status_code == 200
    return response.json()
