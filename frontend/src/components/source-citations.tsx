import { Citation } from "@/lib/types";

type SourceCitationsProps = {
  citations: Citation[];
};

export function SourceCitations({ citations }: SourceCitationsProps) {
  if (!citations.length) {
    return null;
  }

  return (
    <div className="mt-4 grid gap-3">
      {citations.map((citation, index) => (
        <article
          key={`${citation.document_id}-${index}`}
          className="rounded-[1.25rem] border border-[#efd8c8] bg-[#fffaf6] p-4"
        >
          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#9e5a34]">
            <span>{citation.filename}</span>
            <span>Score {citation.score.toFixed(2)}</span>
            {citation.page_number ? <span>Page {citation.page_number}</span> : null}
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-700">{citation.excerpt}</p>
        </article>
      ))}
    </div>
  );
}