"""Login / identity helpers."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants.error_codes import AppError, ErrorCode
from src.constants.messages import LOGIN_FAILED
from src.models import User
from src.utils.jwt import create_access_token
from src.utils.password import verify_password
from src.utils.serializers import user_out


def authenticate(db: Session, email: str, password: str) -> tuple[str, dict]:
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(ErrorCode.UNAUTHORIZED, LOGIN_FAILED)
    token = create_access_token(user)
    return token, user_out(user)


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppError(ErrorCode.UNAUTHORIZED)
    return user
