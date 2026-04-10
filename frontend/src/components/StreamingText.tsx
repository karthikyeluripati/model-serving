import { useEffect, useState } from "react";

interface Props {
  text: string;
  streaming: boolean;
}

export function StreamingText({ text, streaming }: Props) {
  const [showCursor, setShowCursor] = useState(true);

  useEffect(() => {
    if (!streaming) {
      setShowCursor(false);
      return;
    }
    const id = setInterval(() => setShowCursor((v) => !v), 530);
    return () => clearInterval(id);
  }, [streaming]);

  return (
    <span className="whitespace-pre-wrap break-words">
      {text}
      {streaming && (
        <span
          className={`inline-block w-0.5 h-4 ml-0.5 bg-blue-400 align-middle transition-opacity ${
            showCursor ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </span>
  );
}
