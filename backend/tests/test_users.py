from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token, verify_password
from app.models import User, UserRole
from app.schemas import UserCreate
from app.services import EmailAlreadyRegisteredError, create_user
from tests.api_helpers import create_staff_token, register_and_login


def test_create_user_service_creates_privileged_account(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        user = create_user(
            session,
            UserCreate(
                email="AGENT@example.com",
                password="strong-password",
                full_name="Support Agent",
            ),
            UserRole.AGENT,
        )

    assert user.email == "agent@example.com"
    assert user.role == UserRole.AGENT
    assert verify_password("strong-password", user.password_hash)


def test_create_user_service_rejects_duplicate_email(
    session_factory: sessionmaker[Session],
) -> None:
    details = UserCreate(
        email="staff@example.com",
        password="strong-password",
        full_name="Support Staff",
    )
    with session_factory() as session:
        create_user(session, details, UserRole.AGENT)
        try:
            create_user(session, details, UserRole.ADMIN)
        except EmailAlreadyRegisteredError:
            pass
        else:
            raise AssertionError("Duplicate email was accepted")


def test_admin_can_list_only_active_staff(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    admin_token = create_staff_token(session_factory, UserRole.ADMIN)
    with session_factory() as session:
        inactive_agent = User(
            email="inactive@example.com",
            password_hash="unused",
            full_name="Inactive Agent",
            role=UserRole.AGENT,
            is_active=False,
        )
        customer = User(
            email="other-customer@example.com",
            password_hash="unused",
            full_name="Other Customer",
            role=UserRole.CUSTOMER,
        )
        active_agent = User(
            email="active@example.com",
            password_hash="unused",
            full_name="Active Agent",
            role=UserRole.AGENT,
        )
        session.add_all([inactive_agent, customer, active_agent])
        session.commit()

    response = client.get(
        "/api/users/staff",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert [user["email"] for user in response.json()] == [
        "active@example.com",
        "admin@example.com",
    ]


def test_non_admin_cannot_list_staff(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    customer_token = register_and_login(client)
    agent_token = create_staff_token(session_factory)

    for token in (customer_token, agent_token):
        response = client.get(
            "/api/users/staff",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
