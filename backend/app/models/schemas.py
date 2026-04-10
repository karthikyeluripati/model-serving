from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1)
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    stream: bool = False
    system_prompt: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [{"role": "user", "content": "Explain transformers briefly."}],
                "max_tokens": 512,
                "temperature": 0.7,
                "stream": False,
            }
        }
    }


class ChatResponse(BaseModel):
    id: str
    model: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cached: bool = False


class StreamChunk(BaseModel):
    id: str
    delta: str
    finish_reason: Optional[str] = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    backend: str
    model: str
    version: str = "1.0.0"


class MetricsSummary(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    cache_hits: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_prompt_tokens: int
    total_completion_tokens: int
    tokens_per_second: float
    requests_per_minute: float
    error_rate_pct: float
