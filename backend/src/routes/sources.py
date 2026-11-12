from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import Role
from src.controllers import source_controller
from src.middlewares.auth import get_current_user, require_roles
from src.schemas.source import SourceCreate, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
def list_sources(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return source_controller.list_sources(db)


@router.post("", status_code=201)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.ADMIN)),
):
    return source_controller.create_source(db, payload, user)


@router.patch("/{source_id}")
def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.ADMIN)),
):
    return source_controller.update_source(db, source_id, payload, user)
