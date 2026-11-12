from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.constants.roles import Role
from src.controllers import cluster_controller
from src.middlewares.auth import get_current_user, require_permission, require_roles
from src.schemas.cluster import ConfirmClusterRequest, MergeClusterRequest, SplitClusterRequest

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("")
def list_clusters(
    status: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return cluster_controller.list_clusters(db, status, q)


@router.get("/{cluster_id}")
def get_cluster(cluster_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return cluster_controller.get_cluster(db, cluster_id)


@router.post("/{cluster_id}/confirm")
def confirm(
    cluster_id: int,
    payload: ConfirmClusterRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission("cluster:review")),
):
    return cluster_controller.confirm(db, cluster_id, payload, user)


@router.post("/{cluster_id}/split")
def split(
    cluster_id: int,
    payload: SplitClusterRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.ADMIN)),
):
    return cluster_controller.split(db, cluster_id, payload, user)


@router.post("/merge")
def merge(
    payload: MergeClusterRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(Role.ADMIN)),
):
    return cluster_controller.merge(db, payload, user)
