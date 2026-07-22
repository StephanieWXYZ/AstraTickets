from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.db.session import get_db
from app.models import User, UserRole
from app.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/staff", response_model=list[UserRead])
def list_active_staff(
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db)],
) -> list[User]:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    return list(
        session.scalars(
            select(User)
            .where(
                User.is_active.is_(True),
                User.role.in_([UserRole.AGENT, UserRole.ADMIN]),
            )
            .order_by(User.full_name, User.email)
        ).all()
    )
