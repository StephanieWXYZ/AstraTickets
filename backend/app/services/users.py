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
