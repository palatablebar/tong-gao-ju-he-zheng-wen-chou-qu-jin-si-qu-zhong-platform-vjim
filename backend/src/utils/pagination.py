"""Offset/limit pagination shared by every list endpoint."""
from pydantic import BaseModel


class Page(BaseModel):
    items: list
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)


def paginate(query, page: int, page_size: int):
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    total = query.order_by(None).count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, page, page_size
