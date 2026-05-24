interface Props { cwe: string; content: string | null; }

export default function RemediationCard({ cwe, content }: Props) {
  if (!content) return null;
  return (
    <div className="bg-gray-900 border border-teal-800/40 rounded-2xl p-5 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-teal-400 text-lg">🛡</span>
        <h3 className="text-white font-black text-sm">Remediation — {cwe}</h3>
      </div>
      <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{content}</div>
    </div>
  );
}
