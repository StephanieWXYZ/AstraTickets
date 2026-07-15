from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import verify_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register_user(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "CUSTOMER@example.com",
            "password": "strong-password",
            "full_name": "Astra Customer",
        },
    )
    assert response.status_code == 201
    return response.json()


@contextmanager
def database_session() -> Generator[Session, None, None]:
    dependency = app.dependency_overrides[get_db]
    session_generator = dependency()
    session = next(session_generator)
    try:
        yield session
    finally:
        session_generator.close()


def test_register_hashes_password_and_assigns_customer_role(
    client: TestClient,
) -> None:
    data = register_user(client)

    assert data["email"] == "customer@example.com"
    assert data["role"] == "customer"
    assert "password" not in data

    with database_session() as session:
        user = session.scalar(select(User))
        assert user is not None
        assert user.password_hash != "strong-password"
        assert verify_password("strong-password", user.password_hash)


def test_login_returns_token_for_protected_endpoint(client: TestClient) -> None:
    register_user(client)

    login_response = client.post(
        "/api/auth/login",
        data={"username": "customer@example.com", "password": "strong-password"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "customer@example.com"


def test_registration_rejects_duplicate_email(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/auth/register",
        json={
            "email": "customer@example.com",
            "password": "another-password",
            "full_name": "Another Customer",
        },
    )

    assert response.status_code == 409


def test_registration_cannot_choose_privileged_role(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.com",
            "password": "strong-password",
            "full_name": "Not An Admin",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_login_rejects_wrong_password(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/auth/login",
        data={"username": "customer@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
