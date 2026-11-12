from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import Role
from src.controllers import audit_controller
from src.middlewares.auth import require_roles

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
def list_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.ADMIN)),
):
    return audit_controller.list_logs(db, limit)
