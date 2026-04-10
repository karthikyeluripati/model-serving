import { useState, useEffect, useCallback } from "react";
import { fetchMetrics, fetchHealth, type MetricsSummary, type HealthResponse } from "../lib/api";

interface UseMetricsReturn {
  metrics: MetricsSummary | null;
  health: HealthResponse | null;
  loading: boolean;
  refresh: () => void;
}

export function useMetrics(pollIntervalMs = 10_000): UseMetricsReturn {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [m, h] = await Promise.all([fetchMetrics(), fetchHealth()]);
      setMetrics(m);
      setHealth(h);
    } catch {
      // silently fail — the dashboard will show stale data
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollIntervalMs);
    return () => clearInterval(id);
  }, [refresh, pollIntervalMs]);

  return { metrics, health, loading, refresh };
}
