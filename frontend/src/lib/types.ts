export type DocumentSummary = {
  id: string;
  filename: string;
  content_type: string;
  page_count: number;
  chunk_count: number;
  created_at: string;
};

export type Citation = {
  document_id: string;
  filename: string;
  excerpt: string;
  page_number: number | null;
  score: number;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  grounded: boolean;
  quality_control?: QualityControlResult | null;
};

export type QualityControlResult = {
  score: number;
  passed: boolean;
  method: string;
  reason?: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  grounded?: boolean;
  qualityControl?: QualityControlResult | null;
};