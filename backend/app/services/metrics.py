from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Deque

import statistics

from app.models.schemas import MetricsSummary


@dataclass
class RequestRecord:
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    success: bool
    cached: bool
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Thread-safe, in-memory metrics collector with a rolling window."""

    WINDOW_SECONDS = 3600  # 1 hour rolling window

    def __init__(self) -> None:
        self._lock = Lock()
        self._records: Deque[RequestRecord] = deque()
        self._cache_hits = 0
        self._start_time = time.time()

    def record(
        self,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        success: bool,
        cached: bool = False,
    ) -> None:
        record = RequestRecord(
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            success=success,
            cached=cached,
        )
        with self._lock:
            self._records.append(record)
            if cached:
                self._cache_hits += 1
            self._evict_old()

    def _evict_old(self) -> None:
        cutoff = time.time() - self.WINDOW_SECONDS
        while self._records and self._records[0].timestamp < cutoff:
            self._records.popleft()

    def summary(self) -> MetricsSummary:
        with self._lock:
            self._evict_old()
            records = list(self._records)

        if not records:
            return MetricsSummary(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                cache_hits=self._cache_hits,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                total_prompt_tokens=0,
                total_completion_tokens=0,
                tokens_per_second=0.0,
                requests_per_minute=0.0,
                error_rate_pct=0.0,
            )

        latencies = sorted(r.latency_ms for r in records)
        successful = [r for r in records if r.success]
        failed = [r for r in records if not r.success]

        total_completion = sum(r.completion_tokens for r in records)
        elapsed_seconds = max(time.time() - self._start_time, 1)
        window_seconds = max(
            records[-1].timestamp - records[0].timestamp, 1
        )

        def percentile(data: list[float], p: float) -> float:
            if not data:
                return 0.0
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]

        return MetricsSummary(
            total_requests=len(records),
            successful_requests=len(successful),
            failed_requests=len(failed),
            cache_hits=self._cache_hits,
            avg_latency_ms=round(statistics.mean(latencies), 2),
            p50_latency_ms=round(percentile(latencies, 50), 2),
            p95_latency_ms=round(percentile(latencies, 95), 2),
            p99_latency_ms=round(percentile(latencies, 99), 2),
            total_prompt_tokens=sum(r.prompt_tokens for r in records),
            total_completion_tokens=total_completion,
            tokens_per_second=round(total_completion / elapsed_seconds, 2),
            requests_per_minute=round(len(records) / window_seconds * 60, 2),
            error_rate_pct=round(len(failed) / len(records) * 100, 2),
        )


# Singleton
metrics_collector = MetricsCollector()
