#!/usr/bin/env python
"""Worker 健康检查：优先读 Celery beat 写入的 Redis 心跳，兜底 celery inspect ping。"""
import os
import sys
import time

import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")


def heartbeat_ok() -> bool:
    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        value = client.get("dedupwire:worker:heartbeat")
        if not value:
            return False
        return (time.time() - float(value)) < 90
    except Exception:  # noqa: BLE001
        return False


def celery_ok() -> bool:
    try:
        from src.config.celery_app import celery_app

        replies = celery_app.control.ping(timeout=3)
        return bool(replies)
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    if heartbeat_ok() or celery_ok():
        print("worker healthy")
        return 0
    print("worker unhealthy: no heartbeat and no celery pong")
    return 1


if __name__ == "__main__":
    sys.exit(main())
