"""写操作限流：每个登录用户每分钟 120 次（跨切限流，防误触批量脚本）。"""
import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.constants.error_codes import ErrorCode
from src.constants.messages import RATE_LIMITED
from src.utils.ratelimit import hit

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
LIMIT_PER_MINUTE = 120


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in WRITE_METHODS and not request.url.path.endswith("/auth/login"):
            claims = getattr(request.state, "user_claims", None)
            identity = claims.get("email") if claims else (request.client.host if request.client else "anon")
            key = f"dedupwire:ratelimit:{identity}"
            count, _ = hit(key, LIMIT_PER_MINUTE, 60)
            if count > LIMIT_PER_MINUTE:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": ErrorCode.RATE_LIMITED.value,
                        "message": RATE_LIMITED,
                        "request_id": getattr(request.state, "request_id", None),
                    },
                    headers={"Retry-After": "60"},
                )
        return await call_next(request)
