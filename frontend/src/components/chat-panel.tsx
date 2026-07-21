"use client";

import { useState } from "react";

import { ChatMessage } from "@/lib/types";
import { SourceCitations } from "@/components/source-citations";

type ChatPanelProps = {
  messageCount: number;
  hasDocuments: boolean;
  pending: boolean;
  error: string | null;
  messages: ChatMessage[];
  onAsk: (question: string) => Promise<void>;
};

export function ChatPanel({
  messageCount,
  hasDocuments,
  pending,
  error,
  messages,
  onAsk,
}: ChatPanelProps) {
  const [question, setQuestion] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || pending || !hasDocuments) {
      return;
    }

    setQuestion("");
    await onAsk(trimmed);
  }

  return (
    <section className="rounded-[2rem] border border-[#1b2731]/10 bg-[#0f172a] p-6 text-white shadow-[0_24px_80px_rgba(15,23,42,0.18)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#f6b38b]">
            Grounded chat
          </p>
          <h2 className="mt-3 text-2xl font-semibold">Ask the collection</h2>
          <p className="mt-2 max-w-lg text-sm leading-6 text-slate-300">
            Answers are generated only from retrieved document chunks. If the
            evidence is weak, the assistant should refuse to guess.
          </p>
        </div>
        <div className="rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-slate-200">
          {messageCount} messages
        </div>
      </div>

      <div className="mt-6 space-y-4 rounded-[1.75rem] bg-white/5 p-4">
        {!messages.length ? (
          <div className="rounded-[1.5rem] border border-white/10 bg-white/5 px-4 py-6 text-sm text-slate-300">
            Ask about a fact, definition, summary, or comparison after you index
            at least one document.
          </div>
        ) : null}

        {messages.map((message) => (
          <article
            key={message.id}
            className={
              message.role === "user"
                ? "ml-auto max-w-2xl rounded-[1.5rem] bg-[#f97316] px-5 py-4 text-slate-950"
                : message.role === "system"
                  ? "max-w-2xl rounded-[1.5rem] border border-yellow-300/30 bg-yellow-200/10 px-5 py-4 text-yellow-100"
                  : "max-w-2xl rounded-[1.5rem] bg-white px-5 py-4 text-slate-900"
            }
          >
            <div className="text-xs font-semibold uppercase tracking-[0.18em] opacity-70">
              {message.role}
              {message.role === "assistant" ? (
                <span className="ml-2">
                  {message.grounded ? "grounded" : "not grounded"}
                </span>
              ) : null}
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6">
              {message.content}
            </p>
            {message.role === "assistant" && message.citations?.length ? (
              <SourceCitations citations={message.citations} />
            ) : null}
          </article>
        ))}
      </div>

      <form className="mt-6 space-y-3" onSubmit={handleSubmit}>
        <textarea
          className="min-h-32 w-full rounded-[1.5rem] border border-white/10 bg-white/5 px-4 py-4 text-sm leading-6 text-white outline-none transition placeholder:text-slate-400 focus:border-[#f97316]"
          placeholder={
            hasDocuments
              ? "What does the collection say about..."
              : "Upload at least one document before asking a question."
          }
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={!hasDocuments || pending}
        />
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm text-slate-300">
            {error ?? "Citations appear beneath each grounded answer."}
          </div>
          <button
            className="inline-flex items-center justify-center rounded-full bg-[#f97316] px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-[#fb923c] disabled:cursor-not-allowed disabled:bg-slate-500 disabled:text-slate-200"
            type="submit"
            disabled={!hasDocuments || pending || !question.trim()}
          >
            {pending ? "Searching..." : "Send"}
          </button>
        </div>
      </form>
    </section>
  );
}