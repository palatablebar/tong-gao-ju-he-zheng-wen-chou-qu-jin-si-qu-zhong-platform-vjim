from sqlalchemy.orm import Session

from src.schemas.auth import LoginRequest
from src.services import auth_service
from src.utils.serializers import user_out


def login(db: Session, payload: LoginRequest) -> dict:
    token, user = auth_service.authenticate(db, payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer", "user": user}


def me(user) -> dict:
    return user_out(user)
