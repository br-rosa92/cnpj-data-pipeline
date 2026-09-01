"""Configuration for the CNPJ API service."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class APIConfig:
    database_url: str
    api_keys: list[str] = field(default_factory=list)
    rate_limit_per_key: int = 100
    rate_limit_global: int = 1000
    redis_url: str = ""
    statement_timeout_ms: int = 30000
    max_pool_connections: int = 4
    heavy_capacity: int = 2
    page_size_max: int = 50
    offset_max: int = 5000
    batch_score_max: int = 200
    request_timeout_s: int = 30

    @classmethod
    def from_env(cls) -> "APIConfig":
        keys = [k.strip() for k in os.getenv("CNPJ_API_KEYS", "").split(",") if k.strip()]
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            api_keys=keys,
            rate_limit_per_key=int(os.getenv("CNPJ_RATE_LIMIT_PER_KEY", "100")),
            rate_limit_global=int(os.getenv("CNPJ_RATE_LIMIT_GLOBAL", "1000")),
            redis_url=os.getenv("REDIS_URL", ""),
            statement_timeout_ms=int(os.getenv("CNPJ_STATEMENT_TIMEOUT_MS", "30000")),
            max_pool_connections=int(os.getenv("CNPJ_MAX_POOL", "4")),
            heavy_capacity=int(os.getenv("CNPJ_HEAVY_CONCURRENCY", "2")),
            page_size_max=int(os.getenv("CNPJ_PAGE_SIZE_MAX", "50")),
            offset_max=int(os.getenv("CNPJ_OFFSET_MAX", "5000")),
            batch_score_max=int(os.getenv("CNPJ_BATCH_SCORE_MAX", "200")),
            request_timeout_s=int(os.getenv("CNPJ_REQUEST_TIMEOUT_S", "30")),
        )


api_config = APIConfig.from_env()
