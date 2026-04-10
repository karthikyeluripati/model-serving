import { type ChatMessage } from "../hooks/useChat";
import { StreamingText } from "./StreamingText";
import { Bot, User, Zap } from "lucide-react";
import clsx from "clsx";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      className={clsx(
        "flex gap-3 animate-slide-up",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-blue-600" : "bg-gray-700"
        )}
      >
        {isUser ? (
          <User size={16} className="text-white" />
        ) : (
          <Bot size={16} className="text-blue-400" />
        )}
      </div>

      {/* Bubble */}
      <div className={clsx("flex flex-col gap-1 max-w-[80%]", isUser && "items-end")}>
        <div
          className={clsx(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-gray-800 text-gray-100 rounded-tl-sm"
          )}
        >
          {isUser ? (
            <span className="whitespace-pre-wrap break-words">{message.content}</span>
          ) : message.content === "" && message.streaming ? (
            <span className="inline-block w-0.5 h-4 bg-blue-400 animate-pulse" />
          ) : (
            <StreamingText text={message.content} streaming={!!message.streaming} />
          )}
        </div>

        {/* Meta */}
        {!isUser && message.latency_ms && !message.streaming && (
          <div className="flex items-center gap-1 px-1 text-xs text-gray-500">
            <Zap size={10} className="text-yellow-500" />
            <span>{message.latency_ms.toFixed(0)}ms</span>
            {message.cached && (
              <span className="ml-1 px-1.5 py-0.5 bg-green-900/50 text-green-400 rounded text-[10px]">
                cached
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
