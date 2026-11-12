from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import Role
from src.controllers import daily_controller
from src.middlewares.auth import get_current_user, require_roles
from src.schemas.daily import PublishRequest

router = APIRouter(prefix="/daily", tags=["daily"])


@router.get("")
def report(
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return daily_controller.report(db, date)


@router.get("/export")
def export(
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    format: str = Query(default="md", pattern="^(md|csv)$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> Response:
    return daily_controller.export(db, date, format)


@router.post("/publish")
def publish(
    payload: PublishRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.ADMIN)),
):
    return daily_controller.publish(db, payload.date.isoformat(), user)
