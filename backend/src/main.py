"""FastAPI 入口：中间件、异常处理、/api 与无前缀两套路由。"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config.settings import settings
from src.constants.error_codes import AppError, ErrorCode
from src.middlewares.auth import AuthMiddleware
from src.middlewares.rate_limit import RateLimitMiddleware
from src.middlewares.request_context import RequestContextMiddleware
from src.routes import ROUTERS
from src.schemas.common import ErrorEnvelope

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="dedupwire · 通稿聚合正文抽取与近似去重台",
    version="1.0.0",
    description="三江传媒通稿聚合台：信源采集 → 正文抽取 → MinHash/LSH 去重 → 事件时间轴 → 日报。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:18236", "http://127.0.0.1:18236", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestContextMiddleware)


def _envelope(code: str, message: str, request: Request) -> dict:
    return ErrorEnvelope(
        code=code,
        message=message,
        request_id=getattr(request.state, "request_id", None),
    ).model_dump()


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content=_envelope(exc.code.value, exc.message, request)
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    detail = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    )
    return JSONResponse(status_code=422, content=_envelope(ErrorCode.VALIDATION.value, detail, request))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = ErrorCode.NOT_FOUND.value if exc.status_code == 404 else ErrorCode.INTERNAL.value
    return JSONResponse(
        status_code=exc.status_code, content=_envelope(code, str(exc.detail), request)
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger("dedupwire").exception("unhandled error: %s", exc)
    return JSONResponse(
        status_code=500, content=_envelope(ErrorCode.INTERNAL.value, "服务内部错误", request)
    )


for router in ROUTERS:
    app.include_router(router)
    app.include_router(router, prefix="/api")
