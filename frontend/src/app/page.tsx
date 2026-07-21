"use client";

import { useEffect, useState } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { DocumentPanel } from "@/components/document-panel";
import { askQuestion, fetchDocuments, removeDocument, uploadDocument } from "@/lib/api";
import { ChatMessage, Citation, DocumentSummary } from "@/lib/types";

const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;

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
        const extension = file.name.split(".").pop()?.toLowerCase();
        if (extension !== "pdf" && file.type !== "application/pdf") {
          throw new Error("Unsupported file type. Upload a PDF file.");
        }
        if (file.size > MAX_UPLOAD_BYTES) {
          throw new Error("File too large. Maximum size is 50 MB.");
        }
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
          qualityControl: response.quality_control,
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
    <main className="flex h-screen flex-col overflow-hidden bg-[#1f2329] px-3 py-3 text-slate-100 sm:px-4">
      <section className="mx-auto flex w-full max-w-[1600px] items-center justify-between rounded-xl border border-[#343a43] bg-[#1f2329] px-3 py-2">
        <div className="flex items-center gap-2.5">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[conic-gradient(from_210deg_at_50%_50%,#5aa4ff,_#7cc1ff,_#b4d7ff,_#5aa4ff)] text-[10px] font-bold text-[#0f172a]">
            D
          </span>
          <h1 className="text-sm font-semibold tracking-wide text-slate-100">DocTongue</h1>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <button
            type="button"
            className="rounded-full border border-[#3a404a] bg-[#252a31] px-3 py-1.5 text-slate-200 transition hover:bg-[#2c323c]"
          >
            Share
          </button>
          <button
            type="button"
            className="rounded-full border border-[#3a404a] bg-[#252a31] px-3 py-1.5 text-slate-200 transition hover:bg-[#2c323c]"
          >
            Settings
          </button>
        </div>
      </section>

      <section className="mx-auto mt-3 flex min-h-0 w-full max-w-[1600px] flex-1 overflow-hidden rounded-xl border border-[#343a43] bg-[#252a31]">
        <div className="grid h-full min-h-0 w-full lg:grid-cols-[320px_1fr]">
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
            hasDocuments={documents.length > 0}
            pending={chatPending}
            error={chatError}
            messages={messages}
            onAsk={handleAsk}
          />
        </div>
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
