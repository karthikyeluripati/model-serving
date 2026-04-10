import { useMetrics } from "../hooks/useMetrics";
import { Activity, Zap, Database, AlertTriangle, RefreshCw } from "lucide-react";
import clsx from "clsx";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  highlight?: boolean;
}

function StatCard({ label, value, sub, icon, highlight }: StatCardProps) {
  return (
    <div className={clsx(
      "rounded-xl p-4 border flex flex-col gap-2",
      highlight ? "bg-blue-900/30 border-blue-700/50" : "bg-gray-800/60 border-gray-700/50"
    )}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400 font-medium">{label}</span>
        <span className="text-gray-500">{icon}</span>
      </div>
      <div>
        <span className="text-2xl font-bold text-white">{value}</span>
        {sub && <span className="ml-1 text-xs text-gray-500">{sub}</span>}
      </div>
    </div>
  );
}

export function MetricsDashboard() {
  const { metrics, health, loading, refresh } = useMetrics(10_000);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500 text-sm">
        Loading metrics...
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-blue-400" />
          <span className="text-sm font-semibold text-gray-200">System Metrics</span>
          {health && (
            <span className={clsx(
              "text-xs px-2 py-0.5 rounded-full",
              health.status === "ok" ? "bg-green-900/50 text-green-400" : "bg-red-900/50 text-red-400"
            )}>
              {health.status}
            </span>
          )}
        </div>
        <button
          onClick={refresh}
          className="text-gray-500 hover:text-gray-300 transition-colors"
          title="Refresh"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {health && (
        <div className="text-xs text-gray-500 border border-gray-800 rounded-lg px-3 py-2">
          <span className="text-gray-400">Backend:</span>{" "}
          <span className="text-blue-400 font-mono">{health.backend}</span>
          {" · "}
          <span className="text-gray-400">Model:</span>{" "}
          <span className="text-purple-400 font-mono truncate">{health.model}</span>
        </div>
      )}

      {metrics ? (
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            label="Total Requests"
            value={metrics.total_requests}
            icon={<Activity size={14} />}
          />
          <StatCard
            label="Avg Latency"
            value={metrics.avg_latency_ms.toFixed(0)}
            sub="ms"
            icon={<Zap size={14} />}
            highlight
          />
          <StatCard
            label="P95 Latency"
            value={metrics.p95_latency_ms.toFixed(0)}
            sub="ms"
            icon={<Zap size={14} />}
          />
          <StatCard
            label="Cache Hits"
            value={metrics.cache_hits}
            icon={<Database size={14} />}
          />
          <StatCard
            label="Tokens/sec"
            value={metrics.tokens_per_second.toFixed(1)}
            icon={<Activity size={14} />}
            highlight
          />
          <StatCard
            label="Error Rate"
            value={`${metrics.error_rate_pct.toFixed(1)}%`}
            icon={<AlertTriangle size={14} />}
          />
          <StatCard
            label="Req/min"
            value={metrics.requests_per_minute.toFixed(1)}
            icon={<Activity size={14} />}
          />
          <StatCard
            label="Total Tokens"
            value={(metrics.total_completion_tokens + metrics.total_prompt_tokens).toLocaleString()}
            icon={<Database size={14} />}
          />
        </div>
      ) : (
        <div className="text-center text-sm text-gray-500 py-6">
          No metrics yet. Send a message to start tracking.
        </div>
      )}
    </div>
  );
}
