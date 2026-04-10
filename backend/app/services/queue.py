"""
Simple async request queue with concurrency control.
Prevents thundering herd on cold starts and rate limit pressure.
"""
from __future__ import annotations

import asyncio
from app.core.logging import get_logger

logger = get_logger(__name__)

# Allow up to N concurrent inference calls
MAX_CONCURRENT = 10
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)
_queue_depth = 0


async def enqueue(coro):
    """Wrap a coroutine with semaphore-based concurrency limiting."""
    global _queue_depth
    _queue_depth += 1
    logger.debug("queue_enqueued", depth=_queue_depth)

    try:
        async with _semaphore:
            _queue_depth -= 1
            return await coro
    except Exception:
        _queue_depth = max(0, _queue_depth - 1)
        raise


def queue_stats() -> dict:
    return {
        "max_concurrent": MAX_CONCURRENT,
        "current_depth": _queue_depth,
        "available_slots": _semaphore._value,
    }
