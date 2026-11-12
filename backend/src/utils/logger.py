"""One-line structured logs (JSON-ish) for the API and worker."""
import json
import logging
import sys

_LOGGER_NAME = "dedupwire"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_event(event: str, **fields) -> None:
    payload = json.dumps(fields, ensure_ascii=False, default=str)
    get_logger().info("%s %s", event, payload)
