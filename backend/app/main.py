from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, metrics
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RateLimitMiddleware, RequestIDMiddleware

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        backend=settings.inference_backend,
        model=settings.active_model,
        cache=settings.cache_enabled,
        rate_limit=settings.rate_limit_enabled,
    )
    yield
    logger.info("shutdown")


app = FastAPI(
    title="LLM Serving API",
    description="Production-grade LLM inference with streaming, caching, and observability.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware (order matters: outermost first) ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router, tags=["inference"])
app.include_router(health.router, tags=["system"])
app.include_router(metrics.router, tags=["observability"])


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "llm-serving", "version": "1.0.0", "docs": "/docs"}
