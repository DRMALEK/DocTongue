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
    ? "Choose PDF"
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
    <section className="h-full bg-[var(--dt-bg-panel)] p-3 text-[var(--dt-text-primary)] lg:border-r lg:border-[var(--dt-border-base)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-wide text-[var(--dt-text-secondary)]">
            Sources
          </p>
        </div>
        <div className="rounded-md border border-[var(--dt-border-inner)] bg-[var(--dt-bg-surface)] px-2 py-0.5 text-xs text-[var(--dt-text-tertiary)]">
          {documents.length} docs
        </div>
      </div>

      <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-full border border-[var(--dt-border-inner)] bg-[var(--dt-bg-surface)] px-4 py-2 text-center transition hover:bg-[var(--dt-bg-surface-hover)]">
          <span className="text-sm font-medium text-[var(--dt-text-primary)]">+ {uploadLabel}</span>
          <span className="mt-1 text-xs text-[var(--dt-text-muted)]">PDF only, max 50 MB</span>
          <input
            className="sr-only"
            type="file"
            name="files"
            accept=".pdf,application/pdf"
            multiple
            onChange={(event) => {
              setSelectedFiles(Array.from(event.target.files ?? []));
            }}
          />
        </label>

        <button
          className="inline-flex w-full items-center justify-center rounded-full border border-[var(--dt-border-inner)] bg-[var(--dt-bg-surface)] px-4 py-2 text-sm font-semibold text-[var(--dt-text-primary)] transition hover:bg-[var(--dt-bg-msg-assistant)] disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          disabled={!selectedFiles.length || uploadPending}
        >
          {uploadPending ? "Indexing..." : "Upload"}
        </button>
      </form>

      {error ? (
        <div className="mt-3 rounded-lg border border-red-400/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      <div className="mt-5 space-y-2.5">
        {loading ? (
          <div className="rounded-lg border border-[var(--dt-border-inner)] bg-[var(--dt-bg-surface)] px-3 py-3 text-sm text-[var(--dt-text-tertiary)]">
            Loading...
          </div>
        ) : null}

        {!loading && !documents.length ? (
          <div className="rounded-lg border border-[var(--dt-border-inner)] bg-[var(--dt-bg-surface)] px-3 py-3 text-sm text-[var(--dt-text-tertiary)]">
            No docs yet.
          </div>
        ) : null}

        {documents.map((document) => (
          <article
            key={document.id}
            className="rounded-lg border border-[var(--dt-border-inner)] bg-[var(--dt-bg-surface)] p-3"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-sm font-medium text-[var(--dt-text-primary)]">
                  {document.filename}
                </h3>
                <p className="mt-1 text-xs text-[var(--dt-text-muted)]">
                  {document.page_count} pages • {document.chunk_count} chunks
                </p>
              </div>
              <button
                className="rounded-full border border-[var(--dt-border-btn)] px-2.5 py-1 text-xs font-medium text-[var(--dt-text-tertiary)] transition hover:border-red-400 hover:text-red-200 disabled:cursor-not-allowed disabled:opacity-60"
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