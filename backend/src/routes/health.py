from datetime import datetime, timezone

import redis
from fastapi import APIRouter
from sqlalchemy import text

from src.config.database import SessionLocal
from src.config.settings import settings

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict:
    db_ok = False
    redis_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:  # noqa: BLE001 - reported as boolean
        db_ok = False
    try:
        redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2).ping()
        redis_ok = True
    except Exception:  # noqa: BLE001 - reported as boolean
        redis_ok = False
    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "brand": settings.APP_NAME,
        "db": db_ok,
        "redis": redis_ok,
        "time": datetime.now(timezone.utc).isoformat(),
    }
