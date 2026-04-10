import { useState, useRef, type KeyboardEvent } from "react";
import { Send, Square } from "lucide-react";
import clsx from "clsx";

interface Props {
  onSend: (content: string) => void;
  onAbort: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function InputBar({ onSend, onAbort, isStreaming, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  };

  return (
    <div className="border-t border-gray-800 bg-gray-950 px-4 py-3">
      <div className="flex items-end gap-2 max-w-3xl mx-auto">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Message the AI... (Shift+Enter for newline)"
          disabled={disabled}
          rows={1}
          className={clsx(
            "flex-1 resize-none rounded-xl bg-gray-800 border border-gray-700 px-4 py-3",
            "text-sm text-gray-100 placeholder-gray-500 leading-relaxed",
            "focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500",
            "transition-colors min-h-[48px] max-h-40",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        />

        {isStreaming ? (
          <button
            onClick={onAbort}
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-red-600 hover:bg-red-500 flex items-center justify-center transition-colors"
            title="Stop generation"
          >
            <Square size={16} className="text-white" fill="white" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            className={clsx(
              "flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors",
              value.trim() && !disabled
                ? "bg-blue-600 hover:bg-blue-500 text-white"
                : "bg-gray-800 text-gray-600 cursor-not-allowed"
            )}
            title="Send (Enter)"
          >
            <Send size={16} />
          </button>
        )}
      </div>
      <p className="text-center text-xs text-gray-600 mt-2">
        Enter to send · Shift+Enter for newline · LLM Serving v1.0
      </p>
    </div>
  );
}
