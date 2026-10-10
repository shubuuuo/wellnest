"use client";

import { useEffect, useRef, useState } from "react";
import Card from "./Card";
import { API_URL, api } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };
type Status = { ollama: boolean; chat_model: boolean; embed_model: boolean };

const SUGGESTIONS = [
  "Which models can learn online?",
  "Which model performed best?",
  "What do recall and F1 mean?",
  "Why can't Random Forest learn online?",
];

export default function ChatTab({ dataset }: { dataset: string }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .get<Status>("/chat/status")
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy) return;
    const history: Msg[] = [...messages, { role: "user", content: question }];
    setMessages([...history, { role: "assistant", content: "" }]);
    setInput("");
    setBusy(true);
    setProblem(null);
    try {
      const response = await fetch(`${API_URL}/chat?dataset=${dataset}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });
      if (!response.ok || !response.body) {
        const err = await response.json().catch(() => null);
        throw new Error(err?.message ?? "The assistant is not available.");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let answer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        answer += decoder.decode(value, { stream: true });
        setMessages([...history, { role: "assistant", content: answer }]);
      }
    } catch (e) {
      setProblem(e instanceof Error ? e.message : "Something went wrong");
      setMessages(history); // drop the empty answer bubble
    } finally {
      setBusy(false);
    }
  }

  const notReady =
    status && (!status.ollama || !status.chat_model || !status.embed_model);

  return (
    <Card title="Assistant">
      {notReady && (
        <p className="mb-3 rounded-md bg-brand-soft p-3 text-sm">
          {!status.ollama
            ? "Ollama is not running. Start it (ollama serve) and refresh."
            : `Missing model: ${[
                !status.chat_model && "ollama pull qwen2.5:3b",
                !status.embed_model && "ollama pull bge-m3",
              ]
                .filter(Boolean)
                .join("  and  ")}`}
        </p>
      )}

      <div className="h-96 space-y-3 overflow-y-auto rounded-md border border-line p-3">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-muted">
              Ask about this app, its dataset, its models or its scores.
            </p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-line px-3 py-1 text-xs hover:border-brand hover:text-brand"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                m.role === "user" ? "bg-brand text-white" : "bg-line text-ink"
              }`}
            >
              {m.content ||
                (busy && i === messages.length - 1 ? "Thinking…" : "")}
            </div>
          </div>
        ))}
        <div ref={bottom} />
      </div>

      {problem && <p className="mt-3 text-sm text-brand">{problem}</p>}

      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 rounded-md border border-line bg-surface px-3 py-2 text-sm"
          placeholder="Ask a question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
        />
        <button
          onClick={() => send(input)}
          disabled={busy || !input.trim()}
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
      <p className="mt-3 text-xs text-muted">
        Educational demo, not medical advice. The assistant is a small local
        model and can be wrong, so check numbers in the Models tab.
      </p>
    </Card>
  );
}
