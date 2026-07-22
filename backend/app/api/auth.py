from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserRead
from app.services import EmailAlreadyRegisteredError, create_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    session: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        return create_user(session, user_data)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="Email is already registered")


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_db)],
) -> Token:
    email = form_data.username.lower()
    user = session.scalar(select(User).where(User.email == email))
    if (
        user is None
        or not user.is_active
        or not verify_password(form_data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> User:
    return current_user
