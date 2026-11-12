"""Typed application errors mapped to HTTP status codes by the global handler."""
from enum import Enum


class ErrorCode(str, Enum):
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION = "VALIDATION"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL = "INTERNAL"


DEFAULT_STATUS = {
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION: 422,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.INTERNAL: 500,
}


class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str | None = None, status_code: int | None = None):
        self.code = code
        self.message = message or code.value
        self.status_code = status_code or DEFAULT_STATUS[code]
        super().__init__(self.message)
