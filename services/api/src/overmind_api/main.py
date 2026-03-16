import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import graph, metrics

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: try to init DB pool, but don't fail if DB isn't available
    try:
        from .db import init_pool
        await init_pool()
        logger.info("Database pool initialized")
    except Exception:
        logger.warning("Database not available — API will return empty results")
    yield
    # Shutdown
    try:
        from .db import close_pool
        await close_pool()
    except Exception:
        pass


app = FastAPI(title="OVERMIND Intelligence API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.router)
app.include_router(metrics.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
