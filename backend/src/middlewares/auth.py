"""JWT bearer middleware + role dependencies.

Nginx 会剥掉 /api 前缀，所以路由在 backend 上是 /auth/login、/sources 等；
同时为了便于直连调试，main 里也挂了 /api 别名，PUBLIC_PATHS 两套都放行。
"""
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.database import get_db
from src.constants.error_codes import AppError, ErrorCode
from src.constants.messages import NEED_LOGIN, NO_PERMISSION
from src.constants.roles import Role, role_can
from src.models import User
from src.schemas.common import ErrorEnvelope
from src.services import auth_service
from src.utils.jwt import TokenError, decode_access_token

PUBLIC_PATHS = {
    "/",
    "/health",
    "/api/health",
    "/auth/login",
    "/api/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}
PUBLIC_PREFIXES = ("/docs", "/redoc")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user_claims = None
        header = request.headers.get("authorization") or ""
        if header.lower().startswith("bearer "):
            try:
                request.state.user_claims = decode_access_token(header[7:].strip())
            except TokenError:
                request.state.user_claims = None
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES) or request.method == "OPTIONS":
            return await call_next(request)
        if request.state.user_claims is None:
            payload = ErrorEnvelope(
                code=ErrorCode.UNAUTHORIZED.value,
                message=NEED_LOGIN,
                request_id=getattr(request.state, "request_id", None),
            )
            return JSONResponse(status_code=401, content=payload.model_dump())
        return await call_next(request)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    claims = getattr(request.state, "user_claims", None)
    if not claims or not claims.get("sub"):
        raise AppError(ErrorCode.UNAUTHORIZED, NEED_LOGIN)
    return auth_service.get_user(db, int(claims["sub"]))


def require_roles(*roles: Role):
    """FastAPI dependency factory: role gate on top of the JWT."""
    allowed = {role.value if isinstance(role, Role) else role for role in roles}

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise AppError(ErrorCode.FORBIDDEN, NO_PERMISSION)
        return user

    return dependency


def require_permission(permission: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not role_can(user.role, permission):
            raise AppError(ErrorCode.FORBIDDEN, NO_PERMISSION)
        return user

    return dependency
