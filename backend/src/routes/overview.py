from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import overview_controller
from src.middlewares.auth import get_current_user

router = APIRouter(tags=["overview"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return overview_controller.get_overview(db)
