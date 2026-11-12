"""Common response envelopes."""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class PageOut(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class MessageOut(BaseModel):
    message: str
