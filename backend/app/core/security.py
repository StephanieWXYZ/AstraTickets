from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    return password_hash.verify(password, encoded_hash)


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> int:
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("Token subject is missing")

    try:
        return int(subject)
    except ValueError as error:
        raise jwt.InvalidTokenError("Token subject is invalid") from error

