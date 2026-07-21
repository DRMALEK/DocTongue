"use client";

import { useState } from "react";

import { DocumentSummary } from "@/lib/types";

type DocumentPanelProps = {
  documents: DocumentSummary[];
  loading: boolean;
  uploadPending: boolean;
  deletingId: string | null;
  error: string | null;
  onUpload: (files: File[]) => Promise<void>;
  onDelete: (documentId: string) => Promise<void>;
};

export function DocumentPanel({
  documents,
  loading,
  uploadPending,
  deletingId,
  error,
  onUpload,
  onDelete,
}: DocumentPanelProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const uploadLabel = !selectedFiles.length
    ? "Choose PDF, TXT, or MD files"
    : selectedFiles.length === 1
      ? selectedFiles[0].name
      : `${selectedFiles.length} files selected`;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFiles.length || uploadPending) {
      return;
    }

    const form = event.currentTarget;

    await onUpload(selectedFiles);
    setSelectedFiles([]);
    form.reset();
  }

  return (
    <section className="rounded-[2rem] border border-white/60 bg-white/85 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[#b04d1a]">
            Collection
          </p>
          <h2 className="mt-3 text-2xl font-semibold text-slate-900">
            Document library
          </h2>
          <p className="mt-2 max-w-sm text-sm leading-6 text-slate-600">
            Upload files into a shared collection. Every answer is grounded only
            in indexed content from these documents.
          </p>
        </div>
        <div className="rounded-full bg-[#fff1e8] px-4 py-2 text-sm font-medium text-[#8b3d18]">
          {documents.length} indexed
        </div>
      </div>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-[1.5rem] border border-dashed border-[#d9a07c] bg-[#fff8f2] px-5 py-8 text-center transition hover:border-[#b04d1a] hover:bg-[#fff3e9]">
          <span className="text-base font-medium text-slate-900">{uploadLabel}</span>
          <span className="mt-2 text-sm text-slate-600">
            Multiple files are uploaded one after another.
          </span>
          <input
            className="sr-only"
            type="file"
            name="files"
            accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
            multiple
            onChange={(event) => {
              setSelectedFiles(Array.from(event.target.files ?? []));
            }}
          />
        </label>

        <button
          className="inline-flex w-full items-center justify-center rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          type="submit"
          disabled={!selectedFiles.length || uploadPending}
        >
          {uploadPending ? "Indexing documents..." : "Upload and index"}
        </button>
      </form>

      {error ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mt-8 space-y-3">
        {loading ? (
          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
            Loading indexed documents...
          </div>
        ) : null}

        {!loading && !documents.length ? (
          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
            No documents are indexed yet.
          </div>
        ) : null}

        {documents.map((document) => (
          <article
            key={document.id}
            className="rounded-[1.5rem] border border-slate-200 bg-slate-50/80 p-4"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-base font-semibold text-slate-900">
                  {document.filename}
                </h3>
                <p className="mt-1 text-sm text-slate-600">
                  {document.page_count} pages • {document.chunk_count} chunks
                </p>
              </div>
              <button
                className="rounded-full border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-red-400 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                disabled={deletingId === document.id}
                onClick={() => onDelete(document.id)}
              >
                {deletingId === document.id ? "Deleting..." : "Delete"}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}