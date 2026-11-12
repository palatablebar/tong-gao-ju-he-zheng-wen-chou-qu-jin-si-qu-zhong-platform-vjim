"""Role enum + permission matrix. The frontend mirrors this in src/constants/roles.ts."""
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


ROLE_LABELS = {
    Role.ADMIN.value: "主编",
    Role.ANALYST.value: "编辑",
    Role.VIEWER.value: "只读",
}

# 权限点 -> 允许的角色
PERMISSIONS = {
    "source:write": {Role.ADMIN.value},
    "raw:read": {Role.ADMIN.value, Role.ANALYST.value, Role.VIEWER.value},
    "article:correct": {Role.ADMIN.value, Role.ANALYST.value},
    "cluster:review": {Role.ADMIN.value, Role.ANALYST.value},
    "cluster:split": {Role.ADMIN.value},
    "dedup:run": {Role.ADMIN.value, Role.ANALYST.value},
    "reextract:run": {Role.ADMIN.value, Role.ANALYST.value},
    "event:write": {Role.ADMIN.value, Role.ANALYST.value},
    "daily:export": {Role.ADMIN.value, Role.ANALYST.value, Role.VIEWER.value},
    "audit:read": {Role.ADMIN.value},
}


def role_can(role: str, permission: str) -> bool:
    return role in PERMISSIONS.get(permission, set())
