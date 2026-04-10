import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import { type ChatMessage } from "../hooks/useChat";
import { Bot } from "lucide-react";

interface Props {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export function ChatWindow({ messages, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-6">
        <div className="w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
          <Bot size={32} className="text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-100">LLM Serving System</h2>
          <p className="text-gray-500 text-sm mt-1 max-w-sm">
            Production-grade inference with streaming, caching, and observability.
            Start a conversation below.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 justify-center mt-2">
          {[
            "Explain transformers in simple terms",
            "Write a Python async web scraper",
            "What is vLLM and how does it work?",
          ].map((prompt) => (
            <div
              key={prompt}
              className="text-xs px-3 py-1.5 rounded-full bg-gray-800 border border-gray-700 text-gray-400 cursor-default"
            >
              {prompt}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && messages[messages.length - 1]?.role === "user" && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
              <Bot size={16} className="text-blue-400" />
            </div>
            <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 text-sm">
              <span className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
