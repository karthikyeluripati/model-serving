"""
/chat        → full response
/chat/stream → SSE streaming
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import ChatRequest, ChatResponse
from app.services.cache import response_cache
from app.services.inference import InferenceError, generate, stream_generate, _estimate_tokens
from app.services.metrics import metrics_collector
from app.services.queue import enqueue

router = APIRouter()
logger = get_logger(__name__)


# ── /chat ────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    max_tokens = request.max_tokens or settings.max_tokens_default
    temperature = request.temperature if request.temperature is not None else settings.temperature_default
    model = request.model or settings.active_model

    messages_raw = [m.model_dump() for m in request.messages]

    # Cache check
    cached = response_cache.get(messages_raw, model, max_tokens, temperature)
    if cached:
        metrics_collector.record(
            latency_ms=0.0,
            prompt_tokens=cached.prompt_tokens,
            completion_tokens=cached.completion_tokens,
            success=True,
            cached=True,
        )
        return ChatResponse(
            id=str(uuid.uuid4()),
            model=model,
            content=cached.content,
            prompt_tokens=cached.prompt_tokens,
            completion_tokens=cached.completion_tokens,
            total_tokens=cached.prompt_tokens + cached.completion_tokens,
            latency_ms=0.0,
            cached=True,
        )

    # Inference
    start = time.perf_counter()
    try:
        result: ChatResponse = await asyncio.wait_for(
            enqueue(generate(request)),
            timeout=settings.request_timeout_seconds,
        )
    except asyncio.TimeoutError:
        metrics_collector.record(0, 0, 0, success=False)
        raise HTTPException(status_code=504, detail="Inference timed out.")
    except InferenceError as e:
        metrics_collector.record(0, 0, 0, success=False)
        raise HTTPException(status_code=502, detail=str(e))

    # Store in cache
    response_cache.set(
        messages_raw, model, max_tokens, temperature,
        result.content, result.prompt_tokens, result.completion_tokens,
    )

    metrics_collector.record(
        latency_ms=result.latency_ms,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        success=True,
    )

    return result


# ── /chat/stream ─────────────────────────────────────────────────────────────

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, http_request: Request) -> StreamingResponse:
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    total_tokens = 0

    async def event_generator():
        nonlocal total_tokens
        try:
            async for token in stream_generate(request):
                total_tokens += 1
                chunk = {
                    "id": request_id,
                    "delta": token,
                    "finish_reason": None,
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            # Final event
            latency_ms = (time.perf_counter() - start) * 1000
            done_chunk = {
                "id": request_id,
                "delta": "",
                "finish_reason": "stop",
                "latency_ms": round(latency_ms, 2),
                "total_tokens": total_tokens,
            }
            yield f"data: {json.dumps(done_chunk)}\n\n"
            yield "data: [DONE]\n\n"

            metrics_collector.record(
                latency_ms=latency_ms,
                prompt_tokens=0,      # Hard to count mid-stream
                completion_tokens=total_tokens,
                success=True,
            )

        except InferenceError as e:
            error_chunk = {"error": str(e)}
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            metrics_collector.record(0, 0, 0, success=False)

        except asyncio.CancelledError:
            logger.info("stream_cancelled", request_id=request_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
        },
    )
