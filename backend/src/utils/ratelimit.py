"""Fixed-window rate limiter backed by Redis (fails open when Redis is away)."""
import redis

from src.config.settings import settings
from src.constants.error_codes import AppError, ErrorCode

_client: redis.Redis | None = None


def client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def hit(key: str, limit: int, window_seconds: int = 60) -> tuple[int, int]:
    """Record one hit; returns (count, remaining)."""
    try:
        pipe = client().pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        count, _ = pipe.execute()
        return int(count), max(0, limit - int(count))
    except redis.RedisError:
        return 0, limit


def enforce(key: str, limit: int, message: str) -> None:
    count, _ = hit(key, limit)
    if count > limit:
        raise AppError(ErrorCode.RATE_LIMITED, message)


def worker_heartbeat(value: float) -> None:
    try:
        client().set("dedupwire:worker:heartbeat", value)
    except redis.RedisError:
        pass
