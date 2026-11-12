from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    actor_email: str
    actor_role: str
    action: str
    target_type: str
    target_id: str
    detail: dict
    created_at: datetime
