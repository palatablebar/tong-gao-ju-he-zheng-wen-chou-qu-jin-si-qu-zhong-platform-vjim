"""Small helpers around :class:`AppError`."""
from src.constants.error_codes import AppError, ErrorCode


def not_found(name: str, ident) -> AppError:
    return AppError(ErrorCode.NOT_FOUND, f"记录不存在：{name}#{ident}")


def forbidden(message: str | None = None) -> AppError:
    return AppError(ErrorCode.FORBIDDEN, message)


def bad_request(message: str) -> AppError:
    return AppError(ErrorCode.VALIDATION, message)
