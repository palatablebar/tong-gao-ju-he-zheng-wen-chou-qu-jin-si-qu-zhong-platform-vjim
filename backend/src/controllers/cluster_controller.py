from sqlalchemy.orm import Session

from src.services import cluster_service


def list_clusters(db: Session, status, q) -> dict:
    return cluster_service.list_clusters(db, status=status, q=q)


def get_cluster(db: Session, cluster_id: int) -> dict:
    return cluster_service.get_cluster(db, cluster_id)


def confirm(db: Session, cluster_id: int, payload, actor) -> dict:
    return cluster_service.confirm_representative(db, cluster_id, payload, actor)


def split(db: Session, cluster_id: int, payload, actor) -> dict:
    return cluster_service.split_cluster(db, cluster_id, payload.article_ids, actor)


def merge(db: Session, payload, actor) -> dict:
    return cluster_service.merge_clusters(db, payload.source_cluster_id, payload.target_cluster_id, actor)
