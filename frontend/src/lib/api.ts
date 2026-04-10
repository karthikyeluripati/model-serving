export const API_BASE = import.meta.env.VITE_API_URL ?? "";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  messages: Message[];
  model?: string;
  max_tokens?: number;
  temperature?: number;
  system_prompt?: string;
}

export interface ChatResponse {
  id: string;
  model: string;
  content: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  cached: boolean;
}

export interface MetricsSummary {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  cache_hits: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  tokens_per_second: number;
  requests_per_minute: number;
  error_rate_pct: number;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  backend: string;
  model: string;
  version: string;
}

// ── Non-streaming chat ────────────────────────────────────────────────────────

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }

  return res.json();
}

// ── Streaming chat via SSE ────────────────────────────────────────────────────

export async function* streamChat(
  req: ChatRequest,
  signal?: AbortSignal
): AsyncGenerator<{ delta: string; done: boolean; latency_ms?: number }> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...req, stream: true }),
    signal,
  });

  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Stream failed");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6).trim();
      if (payload === "[DONE]") return;

      try {
        const chunk = JSON.parse(payload);
        if (chunk.error) throw new Error(chunk.error);
        yield {
          delta: chunk.delta ?? "",
          done: chunk.finish_reason === "stop",
          latency_ms: chunk.latency_ms,
        };
      } catch {
        // malformed chunk — skip
      }
    }
  }
}

// ── Observability ─────────────────────────────────────────────────────────────

export async function fetchMetrics(): Promise<MetricsSummary> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Failed to fetch health");
  return res.json();
}
