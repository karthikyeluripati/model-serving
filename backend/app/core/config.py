from __future__ import annotations

from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

# Walk up from this file (app/core/config.py) → app/ → backend/ → project root
_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Inference ────────────────────────────────────────────────
    inference_backend: Literal["vllm", "openai", "anthropic", "gemini"] = "openai"

    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # ── Backend ──────────────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8080
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ── Cache ────────────────────────────────────────────────────
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000

    # ── Rate limiting ────────────────────────────────────────────
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window: int = 60  # seconds

    # ── Generation ───────────────────────────────────────────────
    request_timeout_seconds: int = 120
    max_tokens_default: int = 1024
    temperature_default: float = 0.7

    # ── Observability ────────────────────────────────────────────
    log_level: str = "INFO"
    metrics_enabled: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def active_model(self) -> str:
        mapping = {
            "vllm": self.vllm_model,
            "openai": self.openai_model,
            "anthropic": self.anthropic_model,
        }
        return mapping.get(self.inference_backend, self.openai_model)


settings = Settings()
