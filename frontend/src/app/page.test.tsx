import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "@/app/page";
import * as api from "@/lib/api";
import type { ChatResponse, DocumentSummary } from "@/lib/types";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    askQuestion: vi.fn(),
    fetchDocuments: vi.fn(),
    removeDocument: vi.fn(),
    uploadDocument: vi.fn(),
  };
});

const fetchDocuments = vi.mocked(api.fetchDocuments);
const uploadDocument = vi.mocked(api.uploadDocument);
const askQuestion = vi.mocked(api.askQuestion);

const uploadedDocument: DocumentSummary = {
  id: "doc-1",
  filename: "guide.pdf",
  content_type: "application/pdf",
  page_count: 2,
  chunk_count: 4,
  created_at: "2026-07-21T10:00:00Z",
};

const answer: ChatResponse = {
  answer: "The guide says evidence is attached to each grounded answer.",
  grounded: true,
  citations: [
    {
      document_id: "doc-1",
      filename: "guide.pdf",
      excerpt: "Evidence is attached to each grounded answer.",
      page_number: 2,
      score: 0.92,
    },
  ],
};

describe("Home page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchDocuments.mockReset();
    uploadDocument.mockReset();
    askQuestion.mockReset();
    fetchDocuments.mockResolvedValue([]);
  });

  it("uploads documents, refreshes the collection, and renders grounded chat evidence", async () => {
    fetchDocuments
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([uploadedDocument]);
    uploadDocument.mockResolvedValue(uploadedDocument);
    askQuestion.mockResolvedValue(answer);

    const user = userEvent.setup();
    render(<Home />);

    expect(await screen.findByText("No docs yet.")).toBeInTheDocument();

    const fileInput = screen.getByLabelText(/choose pdf/i);
    const file = new File(["dummy"], "guide.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.click(screen.getByRole("button", { name: /^upload$/i }));

    expect(uploadDocument).toHaveBeenCalledWith(file);
    expect(await screen.findByText("guide.pdf")).toBeInTheDocument();

    const questionInput = screen.getByPlaceholderText(/start typing/i);
    await user.type(questionInput, "What does the guide say about evidence?");
    await user.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findByText(answer.answer)).toBeInTheDocument();
    expect(screen.getAllByText("[1]", { exact: false }).length).toBeGreaterThan(0);
    expect(screen.getAllByText("guide.pdf").length).toBeGreaterThan(1);
    expect(
      screen.queryByText("Evidence is attached to each grounded answer."),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/page 2/i)).not.toBeInTheDocument();

    await waitFor(() => {
      expect(askQuestion).toHaveBeenCalledWith("What does the guide say about evidence?");
    });
  });

  it("shows guardrail notice and blocks unsupported upload formats in UI", async () => {
    const user = userEvent.setup({ applyAccept: false });
    render(<Home />);

    expect(await screen.findByText("No docs yet.")).toBeInTheDocument();

    const fileInput = screen.getByLabelText(/choose pdf/i);
    const txtFile = new File(["dummy"], "notes.txt", { type: "text/plain" });
    await user.upload(fileInput, txtFile);
    await user.click(screen.getByRole("button", { name: /^upload$/i }));

    expect(uploadDocument).not.toHaveBeenCalled();
    expect(
      await screen.findByText("Unsupported file type. Upload a PDF file."),
    ).toBeInTheDocument();
  });

  it("blocks uploads larger than 50 MB in UI", async () => {
    const user = userEvent.setup();
    render(<Home />);

    expect(await screen.findByText("No docs yet.")).toBeInTheDocument();

    const fileInput = screen.getByLabelText(/choose pdf/i);
    const oversizedFile = new File([new Uint8Array(50 * 1024 * 1024 + 1)], "big.pdf", {
      type: "application/pdf",
    });
    await user.upload(fileInput, oversizedFile);
    await user.click(screen.getByRole("button", { name: /^upload$/i }));

    expect(uploadDocument).not.toHaveBeenCalled();
    expect(await screen.findByText("File too large. Maximum size is 50 MB.")).toBeInTheDocument();
  });
});