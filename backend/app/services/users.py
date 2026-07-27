from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User, UserRole
from app.schemas import UserCreate


class EmailAlreadyRegisteredError(ValueError):
    pass


def create_user(
    session: Session,
    user_data: UserCreate,
    role: UserRole = UserRole.CUSTOMER,
) -> User:
    email = user_data.email.lower()
    existing_user = session.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        email=email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=role,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise EmailAlreadyRegisteredError from error

    session.refresh(user)
    return user


def ensure_initial_admin(session: Session) -> User | None:
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.initial_admin_email or not settings.initial_admin_password:
        return None

    email = settings.initial_admin_email.lower()
    existing_user = session.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        return existing_user

    return create_user(
        session,
        UserCreate(
            email=email,
            password=settings.initial_admin_password,
            full_name=settings.initial_admin_name,
        ),
        UserRole.ADMIN,
    )
