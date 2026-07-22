import { Citation } from "@/lib/types";

type SourceCitationsProps = {
  citations: Citation[];
};

export function SourceCitations({ citations }: SourceCitationsProps) {
  if (!citations.length) {
    return null;
  }

  const sourceCitations = Array.from(
    citations.reduce<Map<string, Citation>>((sourcesByDocumentId, citation) => {
      if (!sourcesByDocumentId.has(citation.document_id)) {
        sourcesByDocumentId.set(citation.document_id, citation);
      }
      return sourcesByDocumentId;
    }, new Map()),
  ).map(([, citation]) => citation);

  return (
    <div className="mt-3 rounded-lg border border-[var(--dt-border-inner)] bg-[var(--dt-bg-surface)] p-3">
      <ol className="space-y-1.5 text-sm leading-6 text-[var(--dt-text-tertiary)]">
        {sourceCitations.map((citation, index) => (
          <li key={citation.document_id}>
            <span className="font-semibold text-[var(--dt-text-muted)]">[{index + 1}]</span>{" "}
            <span>{citation.filename}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}