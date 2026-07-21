"use client";

import { useState } from "react";

import { ChatMessage } from "@/lib/types";
import { SourceCitations } from "@/components/source-citations";

type ChatPanelProps = {
  hasDocuments: boolean;
  pending: boolean;
  error: string | null;
  messages: ChatMessage[];
  onAsk: (question: string) => Promise<void>;
};

export function ChatPanel({
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
    <section className="flex h-full min-h-0 flex-col bg-[#252a31] p-3 text-slate-100">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-wide text-slate-200">
            Chat
          </p>
        </div>
      </div>

      <div className="mt-3 flex min-h-0 flex-1 flex-col space-y-3 overflow-y-auto rounded-lg border border-[#343a43] bg-[#232830] p-3">
        {error ? (
          <div className="rounded-lg border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        {!messages.length ? (
          <div className="flex min-h-[18rem] items-center justify-center px-4 py-6 text-center text-base text-slate-400">
            Ask a question after indexing documents.
          </div>
        ) : null}

        {messages.map((message) => (
          <article
            key={message.id}
            className={
              message.role === "user"
                ? "ml-auto max-w-2xl rounded-lg bg-[#1b2027] px-4 py-3 text-slate-100"
                : message.role === "system"
                  ? "max-w-2xl rounded-lg border border-red-400/40 bg-red-500/10 px-4 py-3 text-red-200"
                  : "max-w-2xl rounded-lg border border-[#3a404a] bg-[#2a3039] px-4 py-3 text-slate-100"
            }
          >
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
              {message.role}
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

      <form className="mt-4" onSubmit={handleSubmit}>
        <div className="flex items-center gap-2 rounded-xl border border-[#3a404a] bg-[#20252c] p-2">
          <textarea
            className="min-h-10 flex-1 resize-none bg-transparent px-2 py-1 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-500"
            placeholder={
              hasDocuments
                ? "Start typing..."
                : "Upload at least one document before asking a question."
            }
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            disabled={!hasDocuments || pending}
            rows={1}
          />
          <button
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#4a5563] bg-[#2a3039] text-slate-100 transition hover:bg-[#343b46] disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={!hasDocuments || pending || !question.trim()}
            aria-label={pending ? "Searching" : "Send"}
          >
            <span aria-hidden="true">➜</span>
          </button>
        </div>
      </form>
    </section>
  );
}