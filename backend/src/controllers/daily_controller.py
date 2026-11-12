from fastapi import Response
from sqlalchemy.orm import Session

from src.services import daily_service


def report(db: Session, date_text: str) -> dict:
    return daily_service.report(db, date_text)


def export(db: Session, date_text: str, fmt: str) -> Response:
    content, media_type, filename = daily_service.export(db, date_text, fmt)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def publish(db: Session, date_text: str, actor) -> dict:
    return daily_service.publish(db, date_text, actor)
