"""Synchronous PostgreSQL access with a bounded connection pool."""

import logging
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
import psycopg2.pool

from api.config import api_config

logger = logging.getLogger(__name__)

_NOT_ALLOWED_TABLES = {
    "pg_",
    "sql_",
    "information_schema",
}


def _parse_url(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path[1:],
        "user": parsed.username,
        "password": parsed.password,
    }


class Database:
    """Threaded connection pool with per-connection statement timeout."""

    def __init__(self, maxconn: int = 4):
        self._url = api_config.database_url
        self._params = _parse_url(self._url)
        self._params["options"] = f"-c statement_timeout={api_config.statement_timeout_ms}"
        self._params["application_name"] = "cnpj-api"
        self._maxconn = maxconn
        self._pool = None

    def _ensure_pool(self):
        if self._pool is None:
            self._pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=self._maxconn, **self._params)

    @contextmanager
    def cursor(self):
        self._ensure_pool()
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def fetch_one(self, sql, params=None):
        with self.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

    def fetch_all(self, sql, params=None):
        with self.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

    def close(self):
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None


db = Database(maxconn=api_config.max_pool_connections)


def validate_identifier(identifier: str) -> None:
    """Reject unsafe identifiers before interpolation in SQL."""
    if identifier.startswith(tuple(_NOT_ALLOWED_TABLES)):
        raise ValueError(f"Identificador nao permitido: {identifier}")
    if not identifier.replace("_", "").isalnum():
        raise ValueError(f"Identificador invalido: {identifier}")
