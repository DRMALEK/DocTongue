"use client";

import { useEffect, useState } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { DocumentPanel } from "@/components/document-panel";
import { askQuestion, fetchDocuments, removeDocument, uploadDocument } from "@/lib/api";
import { ChatMessage, Citation, DocumentSummary } from "@/lib/types";

export default function Home() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [uploadPending, setUploadPending] = useState(false);
  const [deletePendingId, setDeletePendingId] = useState<string | null>(null);
  const [chatPending, setChatPending] = useState(false);
  const [documentError, setDocumentError] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);

  async function loadDocuments() {
    setLoadingDocuments(true);
    setDocumentError(null);
    try {
      const nextDocuments = await fetchDocuments();
      setDocuments(nextDocuments);
    } catch (error) {
      setDocumentError(getErrorMessage(error));
    } finally {
      setLoadingDocuments(false);
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      void loadDocuments();
    });
  }, []);

  async function handleUpload(files: File[]) {
    setUploadPending(true);
    setDocumentError(null);
    try {
      for (const file of files) {
        await uploadDocument(file);
      }
      await loadDocuments();
    } catch (error) {
      setDocumentError(getErrorMessage(error));
    } finally {
      setUploadPending(false);
    }
  }

  async function handleDelete(documentId: string) {
    setDeletePendingId(documentId);
    setDocumentError(null);
    try {
      await removeDocument(documentId);
      setDocuments((current) => current.filter((item) => item.id !== documentId));
    } catch (error) {
      setDocumentError(getErrorMessage(error));
    } finally {
      setDeletePendingId(null);
    }
  }

  async function handleAsk(question: string) {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };
    setMessages((current) => [...current, userMessage]);
    setChatPending(true);
    setChatError(null);

    try {
      const response = await askQuestion(question);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          grounded: response.grounded,
        },
      ]);
    } catch (error) {
      const message = getErrorMessage(error);
      setChatError(message);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "system",
          content: message,
          citations: [] as Citation[],
        },
      ]);
    } finally {
      setChatPending(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-8 sm:px-6 lg:px-8">
      <section className="relative overflow-hidden rounded-[2.5rem] border border-white/70 bg-white/80 px-6 py-10 shadow-[0_30px_120px_rgba(15,23,42,0.12)] backdrop-blur sm:px-8 lg:px-10">
        <div className="absolute inset-x-0 top-0 h-28 bg-[radial-gradient(circle_at_top_left,_rgba(249,115,22,0.22),_transparent_58%),radial-gradient(circle_at_top_right,_rgba(15,23,42,0.12),_transparent_45%)]" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.26em] text-[#b04d1a]">
              DocTongue
            </p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Grounded answers for your private document collection.
            </h1>
            <p className="mt-4 max-w-xl text-base leading-7 text-slate-600 sm:text-lg">
              Upload PDFs or text files, search across the whole collection, and
              inspect the exact passages used to answer each question.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 self-start text-sm text-slate-700 sm:self-auto">
            <div className="rounded-[1.5rem] bg-[#fff4ec] px-4 py-3">
              <div className="font-semibold text-slate-950">{documents.length}</div>
              <div className="mt-1">Indexed documents</div>
            </div>
            <div className="rounded-[1.5rem] bg-slate-900 px-4 py-3 text-slate-100">
              <div className="font-semibold">{messages.length}</div>
              <div className="mt-1">Chat turns</div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-8 lg:grid-cols-[0.95fr_1.25fr]">
        <DocumentPanel
          documents={documents}
          loading={loadingDocuments}
          uploadPending={uploadPending}
          deletingId={deletePendingId}
          error={documentError}
          onUpload={handleUpload}
          onDelete={handleDelete}
        />
        <ChatPanel
          messageCount={messages.length}
          hasDocuments={documents.length > 0}
          pending={chatPending}
          error={chatError}
          messages={messages}
          onAsk={handleAsk}
        />
      </section>
    </main>
  );
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Something went wrong.";
}
