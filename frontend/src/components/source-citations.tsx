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
    <div className="mt-3 rounded-lg border border-[#3a404a] bg-[#20252c] p-3">
      <ol className="space-y-1.5 text-sm leading-6 text-slate-300">
        {sourceFilenames.map((filename, index) => (
          <li key={filename}>
            <span className="font-semibold text-slate-400">[{index + 1}]</span>{" "}
            <span>{filename}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}