import { ChatResponse, DocumentSummary } from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

type DocumentListResponse = {
  documents: DocumentSummary[];
};

type DocumentUploadResponse = {
  document: DocumentSummary;
};

type ApiError = {
  detail?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = "Request failed.";
    try {
      const body = (await response.json()) as ApiError;
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function fetchDocuments(): Promise<DocumentSummary[]> {
  const payload = await request<DocumentListResponse>("/api/documents");
  return payload.documents;
}

export async function uploadDocument(file: File): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);

  const payload = await request<DocumentUploadResponse>("/api/documents", {
    method: "POST",
    body: formData,
  });

  return payload.document;
}

export async function removeDocument(documentId: string): Promise<void> {
  await request<void>(`/api/documents/${documentId}`, {
    method: "DELETE",
  });
}

export async function askQuestion(question: string): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });
}