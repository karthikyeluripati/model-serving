"""
Inference service with:
- vLLM primary backend (OpenAI-compatible API)
- OpenAI fallback
- Anthropic fallback
- Retry logic with exponential backoff
- Token counting
- Streaming support
"""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import AsyncGenerator, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import ChatRequest, ChatResponse, Message

logger = get_logger(__name__)

# ── Token estimation (cheap, no model load) ──────────────────────────────────

def _estimate_tokens(text: str) -> int:
    """~4 chars per token heuristic when tiktoken unavailable."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def _count_messages_tokens(messages: list[Message]) -> int:
    return sum(_estimate_tokens(m.content) for m in messages)


# ── OpenAI-compatible client (covers vLLM + OpenAI) ─────────────────────────

async def _openai_complete(
    request: ChatRequest,
    base_url: str,
    api_key: str,
    model: str,
) -> ChatResponse:
    from openai import AsyncOpenAI, APIError, APITimeoutError

    client = AsyncOpenAI(
        api_key=api_key or "no-key",
        base_url=base_url,
        timeout=settings.request_timeout_seconds,
    )

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    if request.system_prompt:
        messages.insert(0, {"role": "system", "content": request.system_prompt})

    max_tokens = request.max_tokens or settings.max_tokens_default
    temperature = request.temperature if request.temperature is not None else settings.temperature_default

    start = time.perf_counter()
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type((APIError, APITimeoutError, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    ):
        with attempt:
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )

    latency_ms = (time.perf_counter() - start) * 1000
    content = resp.choices[0].message.content or ""
    usage = resp.usage

    return ChatResponse(
        id=resp.id or str(uuid.uuid4()),
        model=resp.model or model,
        content=content,
        prompt_tokens=usage.prompt_tokens if usage else _count_messages_tokens(request.messages),
        completion_tokens=usage.completion_tokens if usage else _estimate_tokens(content),
        total_tokens=usage.total_tokens if usage else 0,
        latency_ms=round(latency_ms, 2),
    )


async def _openai_stream(
    request: ChatRequest,
    base_url: str,
    api_key: str,
    model: str,
) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=api_key or "no-key",
        base_url=base_url,
        timeout=settings.request_timeout_seconds,
    )

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    if request.system_prompt:
        messages.insert(0, {"role": "system", "content": request.system_prompt})

    max_tokens = request.max_tokens or settings.max_tokens_default
    temperature = request.temperature if request.temperature is not None else settings.temperature_default

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# ── Anthropic client ─────────────────────────────────────────────────────────

async def _anthropic_complete(request: ChatRequest) -> ChatResponse:
    import anthropic as sdk

    client = sdk.AsyncAnthropic(api_key=settings.anthropic_api_key)
    model = request.model or settings.anthropic_model

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    system = request.system_prompt or ""
    max_tokens = request.max_tokens or settings.max_tokens_default

    start = time.perf_counter()
    resp = await client.messages.create(
        model=model,
        messages=messages,
        system=system or sdk.NOT_GIVEN,
        max_tokens=max_tokens,
        temperature=request.temperature if request.temperature is not None else settings.temperature_default,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    content = resp.content[0].text if resp.content else ""
    return ChatResponse(
        id=resp.id,
        model=resp.model,
        content=content,
        prompt_tokens=resp.usage.input_tokens,
        completion_tokens=resp.usage.output_tokens,
        total_tokens=resp.usage.input_tokens + resp.usage.output_tokens,
        latency_ms=round(latency_ms, 2),
    )


async def _anthropic_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    import anthropic as sdk

    client = sdk.AsyncAnthropic(api_key=settings.anthropic_api_key)
    model = request.model or settings.anthropic_model
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    system = request.system_prompt or ""
    max_tokens = request.max_tokens or settings.max_tokens_default

    async with client.messages.stream(
        model=model,
        messages=messages,
        system=system or sdk.NOT_GIVEN,
        max_tokens=max_tokens,
        temperature=request.temperature if request.temperature is not None else settings.temperature_default,
    ) as stream:
        async for text in stream.text_stream:
            yield text


# ── Public API ───────────────────────────────────────────────────────────────

class InferenceError(Exception):
    """Raised when all backends fail."""


async def generate(request: ChatRequest) -> ChatResponse:
    """Generate a complete response, falling back across backends."""
    backend = settings.inference_backend
    logger.info("inference_start", backend=backend)

    try:
        if backend == "vllm":
            try:
                return await _openai_complete(
                    request,
                    base_url=f"{settings.vllm_base_url}",
                    api_key="no-key",
                    model=request.model or settings.vllm_model,
                )
            except Exception as e:
                logger.warning("vllm_failed_falling_back", error=str(e))
                # Fall through to openai
                return await _openai_complete(
                    request,
                    base_url="https://api.openai.com/v1",
                    api_key=settings.openai_api_key,
                    model=request.model or settings.openai_model,
                )

        elif backend == "openai":
            return await _openai_complete(
                request,
                base_url="https://api.openai.com/v1",
                api_key=settings.openai_api_key,
                model=request.model or settings.openai_model,
            )

        elif backend == "anthropic":
            return await _anthropic_complete(request)

        else:
            raise InferenceError(f"Unknown backend: {backend}")

    except Exception as e:
        logger.error("inference_failed", error=str(e), backend=backend)
        raise InferenceError(str(e)) from e


async def stream_generate(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Stream tokens from the active backend."""
    backend = settings.inference_backend

    try:
        if backend == "vllm":
            try:
                async for token in _openai_stream(
                    request,
                    base_url=settings.vllm_base_url,
                    api_key="no-key",
                    model=request.model or settings.vllm_model,
                ):
                    yield token
            except Exception as e:
                logger.warning("vllm_stream_failed_falling_back", error=str(e))
                async for token in _openai_stream(
                    request,
                    base_url="https://api.openai.com/v1",
                    api_key=settings.openai_api_key,
                    model=request.model or settings.openai_model,
                ):
                    yield token

        elif backend == "openai":
            async for token in _openai_stream(
                request,
                base_url="https://api.openai.com/v1",
                api_key=settings.openai_api_key,
                model=request.model or settings.openai_model,
            ):
                yield token

        elif backend == "anthropic":
            async for token in _anthropic_stream(request):
                yield token

    except Exception as e:
        logger.error("stream_failed", error=str(e))
        raise InferenceError(str(e)) from e
