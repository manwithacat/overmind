import os
from contextlib import asynccontextmanager

from psycopg_pool import AsyncConnectionPool


def get_db_url() -> str:
    user = os.environ.get("POSTGRES_USER", "overmind")
    password = os.environ.get("POSTGRES_PASSWORD", "overmind-dev")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    db = os.environ.get("POSTGRES_DB", "overmind")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


# Connection pool (initialized on app startup)
_pool: AsyncConnectionPool | None = None


async def init_pool():
    global _pool
    _pool = AsyncConnectionPool(get_db_url(), min_size=2, max_size=10)
    await _pool.open()


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()


@asynccontextmanager
async def get_conn():
    async with _pool.connection() as conn:
        yield conn
