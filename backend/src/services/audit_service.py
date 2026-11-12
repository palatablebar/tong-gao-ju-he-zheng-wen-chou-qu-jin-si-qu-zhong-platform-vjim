"""审计日志：所有写操作都落一条 audit_logs。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import AuditLog


def record(db: Session, user, action: str, target_type: str, target_id, detail: dict | None = None) -> AuditLog:
    log = AuditLog(
        actor_email=getattr(user, "email", "system"),
        actor_role=getattr(user, "role", "system"),
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        detail=detail or {},
    )
    db.add(log)
    return log


def list_logs(db: Session, limit: int = 50) -> list[dict]:
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [
        {
            "id": row.id,
            "actor_email": row.actor_email,
            "actor_role": row.actor_role,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "detail": row.detail,
            "created_at": row.created_at,
        }
        for row in rows
    ]
