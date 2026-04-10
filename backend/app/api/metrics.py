from fastapi import APIRouter
from app.models.schemas import MetricsSummary
from app.services.metrics import metrics_collector
from app.services.cache import response_cache
from app.services.queue import queue_stats

router = APIRouter()


@router.get("/metrics", response_model=MetricsSummary)
async def metrics() -> MetricsSummary:
    return metrics_collector.summary()


@router.get("/metrics/detail")
async def metrics_detail() -> dict:
    return {
        "summary": metrics_collector.summary().model_dump(),
        "cache": response_cache.stats(),
        "queue": queue_stats(),
    }
