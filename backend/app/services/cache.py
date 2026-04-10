from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    content: str
    prompt_tokens: int
    completion_tokens: int
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = time.time()

    def is_expired(self, ttl: int) -> bool:
        return time.time() - self.created_at > ttl


class ResponseCache:
    """LRU-style in-memory cache with TTL expiry."""

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []

    @staticmethod
    def _make_key(messages: list[dict], model: str, max_tokens: int, temperature: float) -> str:
        payload = json.dumps(
            {"messages": messages, "model": model, "max_tokens": max_tokens, "temperature": temperature},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> Optional[CacheEntry]:
        if not settings.cache_enabled:
            return None

        key = self._make_key(messages, model, max_tokens, temperature)
        entry = self._store.get(key)

        if entry is None:
            return None

        if entry.is_expired(settings.cache_ttl_seconds):
            del self._store[key]
            logger.debug("cache_expired", key=key[:8])
            return None

        # Move to end (most recently used)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug("cache_hit", key=key[:8])
        return entry

    def set(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float,
        content: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        if not settings.cache_enabled:
            return

        # Evict LRU if over capacity
        while len(self._store) >= settings.cache_max_size and self._access_order:
            oldest = self._access_order.pop(0)
            self._store.pop(oldest, None)

        key = self._make_key(messages, model, max_tokens, temperature)
        self._store[key] = CacheEntry(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self._access_order.append(key)
        logger.debug("cache_set", key=key[:8], size=len(self._store))

    def stats(self) -> dict:
        return {"size": len(self._store), "max_size": settings.cache_max_size}


# Singleton
response_cache = ResponseCache()
