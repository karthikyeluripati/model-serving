import { useState } from "react";
import { ChatWindow } from "./components/ChatWindow";
import { InputBar } from "./components/InputBar";
import { MetricsDashboard } from "./components/MetricsDashboard";
import { useChat } from "./hooks/useChat";
import { BarChart2, MessageSquare, Trash2 } from "lucide-react";
import clsx from "clsx";

type Tab = "chat" | "metrics";

export default function App() {
  const { messages, isStreaming, error, sendMessage, clearMessages, abort } = useChat();
  const [tab, setTab] = useState<Tab>("chat");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      {/* ── Sidebar ────────────────────────────────────────────── */}
      <aside
        className={clsx(
          "flex flex-col border-r border-gray-800 bg-gray-900 transition-all duration-200",
          sidebarOpen ? "w-72" : "w-0 overflow-hidden"
        )}
      >
        <div className="px-4 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-xs font-bold">
              L
            </div>
            <div>
              <div className="text-sm font-semibold">LLM Serving</div>
              <div className="text-xs text-gray-500">Production System</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="p-3 flex flex-col gap-1">
          {(
            [
              { id: "chat", label: "Chat", icon: <MessageSquare size={16} /> },
              { id: "metrics", label: "Metrics", icon: <BarChart2 size={16} /> },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              onClick={() => setTab(item.id)}
              className={clsx(
                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors w-full text-left",
                tab === item.id
                  ? "bg-blue-600/20 text-blue-400 border border-blue-600/30"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
              )}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex-1 overflow-auto">
          {tab === "metrics" && <MetricsDashboard />}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-800">
          <button
            onClick={clearMessages}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-500 hover:text-red-400 hover:bg-red-900/20 transition-colors w-full"
          >
            <Trash2 size={14} />
            Clear conversation
          </button>
        </div>
      </aside>

      {/* ── Main ───────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-gray-800 bg-gray-900/50">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="text-gray-500 hover:text-gray-300 transition-colors p-1 rounded"
            title="Toggle sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="text-sm font-medium text-gray-300">
            {tab === "chat" ? "Chat" : "System Metrics"}
          </span>
          {isStreaming && (
            <span className="ml-auto text-xs text-blue-400 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
              Generating...
            </span>
          )}
        </header>

        {/* Error banner */}
        {error && (
          <div className="mx-4 mt-3 px-4 py-2 rounded-lg bg-red-900/30 border border-red-700/50 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Content */}
        {tab === "chat" ? (
          <>
            <ChatWindow messages={messages} isStreaming={isStreaming} />
            <InputBar
              onSend={sendMessage}
              onAbort={abort}
              isStreaming={isStreaming}
            />
          </>
        ) : (
          <div className="flex-1 overflow-auto p-6">
            <MetricsDashboard />
          </div>
        )}
      </main>
    </div>
  );
}
