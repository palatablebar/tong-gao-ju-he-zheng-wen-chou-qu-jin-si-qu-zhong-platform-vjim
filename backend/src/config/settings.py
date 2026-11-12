"""Runtime settings shared by the API process, the Celery worker and the seed."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "dedupwire"
    APP_ENV: str = "docker"

    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "dedupwire"
    DB_USER: str = "dedupwire"
    DB_PASSWORD: str = "dedupwire_pw_2026"

    JWT_SECRET: str = "dedupwire-jwt-secret-change-me-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 12

    REDIS_URL: str = "redis://redis:6379/0"
    SEED_DEMO: bool = False

    # ---- 算法 A：正文抽取 ----
    EXTRACT_SCORE_DIVISOR: float = 45.0
    EXTRACT_LOW_CONFIDENCE: float = 0.4
    EXTRACT_MIN_BODY_CHARS: int = 120

    # ---- 算法 B：MinHash + LSH ----
    DEDUP_SIM_THRESHOLD: float = 0.72
    DEDUP_SUSPECT_THRESHOLD: float = 0.55
    DEDUP_NUM_PERM: int = 128
    DEDUP_BANDS: int = 32
    DEDUP_SHINGLE_SIZE: int = 4
    DEDUP_HASH_SEED: int = 20261110
    DEDUP_RATE_LIMIT_PER_MINUTE: int = 10

    # ---- 运行参数 ----
    VAR_DIR: str = "/app/var"
    DEDUP_CLUSTER_MIN_SIZE: int = 2

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
