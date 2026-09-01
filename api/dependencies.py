"""Shared helpers and guardrails: schema validation and rate limiting."""

import time

from fastapi import Header, HTTPException

from api.config import api_config


def normalize_cnpj(raw: str) -> str:
    """Strip non-digits and validate a 14-digit CNPJ. Raises ValueError if invalid."""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) != 14:
        raise ValueError("CNPJ invalido: deve conter 14 digitos")
    return digits


def split_cnpj(cnpj: str) -> tuple[str, str, str]:
    """Split a 14-digit CNPJ into (cnpj_basico, cnpj_ordem, cnpj_dv)."""
    return cnpj[:8], cnpj[8:12], cnpj[12:]


def validate_uf(uf: str | None) -> str | None:
    """Validate Brazilian state code (2 uppercase letters)."""
    if not uf:
        return None
    uf = uf.upper().strip()
    if len(uf) != 2 or not uf.isalpha():
        raise ValueError("UF invalida: use a sigla com 2 letras (ex.: SP)")
    return uf


class SlidingWindowLimiter:
    """Sliding-window rate limiter with an in-memory fallback when Redis is absent."""

    def __init__(self, limit: int, window_s: float = 60.0):
        self.limit = limit
        self.window_s = window_s
        self._hits: dict[str, list[float]] = {}

    def _prune(self, key: str, now: float) -> None:
        cutoff = now - self.window_s
        self._hits[key] = [ts for ts in self._hits.get(key, []) if ts > cutoff]

    def allows(self, key: str) -> bool:
        now = time.monotonic()
        self._prune(key, now)
        if len(self._hits.get(key, [])) >= self.limit:
            return False
        self._hits.setdefault(key, []).append(now)
        return True


class RateLimiter:
    """Redis-backed sliding window with in-memory fallback."""

    def __init__(self):
        self._redis = None
        self._mem = SlidingWindowLimiter(api_config.rate_limit_global)
        self._mem_per_key: dict[str, SlidingWindowLimiter] = {}
        if api_config.redis_url:
            try:
                import redis

                self._redis = redis.Redis.from_url(api_config.redis_url, decode_responses=True)
            except Exception:
                self._redis = None

    def _per_key_limiter(self, key: str) -> SlidingWindowLimiter:
        if key not in self._mem_per_key:
            self._mem_per_key[key] = SlidingWindowLimiter(api_config.rate_limit_per_key)
        return self._mem_per_key[key]

    def allows(self, key: str, scope: str) -> bool:
        if self._redis is not None:
            try:
                return self._allows_redis(key, scope)
            except Exception:
                pass
        if scope == "global":
            return self._mem.allows("g")
        return self._per_key_limiter(key).allows(key)

    def _allows_redis(self, key: str, scope: str) -> bool:
        rkey = f"rl:{scope}:{key}"
        now = time.time()
        limit = api_config.rate_limit_global if scope == "global" else api_config.rate_limit_per_key
        with self._redis.pipeline() as pipe:
            pipe.zremrangebyscore(rkey, 0, now - 60)
            pipe.zcard(rkey)
            count = pipe.execute()[-1]
        if count >= limit:
            return False
        self._redis.zadd(rkey, {str(now): now})
        self._redis.expire(rkey, 120)
        return True


rate_limiter = RateLimiter()


def expect_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """FastAPI dependency: validate the X-Api-Key header."""
    if not x_api_key or x_api_key not in api_config.api_keys:
        raise HTTPException(status_code=401, detail="API key invalida")
    return x_api_key
