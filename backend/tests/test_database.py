import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.url import normalize_database_url
from app.models import User, UserRole


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as database_session:
        yield database_session


def test_create_user(session: Session) -> None:
    user = User(
        email="customer@example.com",
        password_hash="hashed-password",
        full_name="Astra Customer",
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.role is UserRole.CUSTOMER
    assert user.is_active is True


def test_user_email_must_be_unique(session: Session) -> None:
    session.add_all(
        [
            User(
                email="same@example.com",
                password_hash="first-hash",
                full_name="First User",
            ),
            User(
                email="same@example.com",
                password_hash="second-hash",
                full_name="Second User",
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_neon_database_url_uses_psycopg_driver() -> None:
    assert normalize_database_url(
        "postgresql://user:password@example.neon.tech/database"
    ) == "postgresql+psycopg://user:password@example.neon.tech/database"
