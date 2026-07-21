import { Citation } from "@/lib/types";

type SourceCitationsProps = {
  citations: Citation[];
};

export function SourceCitations({ citations }: SourceCitationsProps) {
  if (!citations.length) {
    return null;
  }

  const sourceFilenames = Array.from(
    new Set(citations.map((citation) => citation.filename)),
  );

  return (
    <div className="mt-4 rounded-[1.25rem] border border-[#efd8c8] bg-[#fffaf6] p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#9e5a34]">
        References
      </p>
      <ol className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
        {sourceFilenames.map((filename, index) => (
          <li key={filename}>
            <span className="font-semibold text-[#9e5a34]">[{index + 1}]</span>{" "}
            <span>{filename}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}