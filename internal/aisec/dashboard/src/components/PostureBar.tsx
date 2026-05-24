"use client";
import { SCANNERS } from "@/lib/scanners";
import type { ScannerStatus } from "@/app/page";

interface Props {
  statuses: Record<string, ScannerStatus>;
  loading?: boolean;
}

export default function PostureBar({ statuses, loading }: Props) {
  const total    = Object.values(statuses).reduce((s, r) => s + Object.values(r.counts ?? {}).reduce((a, b) => a + b, 0), 0);
  const critical = Object.values(statuses).reduce((s, r) => s + (r.counts?.CRITICAL ?? 0), 0);
  const high     = Object.values(statuses).reduce((s, r) => s + (r.counts?.HIGH ?? 0), 0);
  const pass     = Object.values(statuses).filter(r => r.status === "pass").length;
  const fail     = Object.values(statuses).filter(r => r.status === "fail").length;

  return (
    <div className="border-b border-gray-800 bg-gray-900/50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6 flex-wrap">
        <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Posture</div>
        {loading ? (
          <span className="text-xs text-gray-600 animate-pulse">Loading…</span>
        ) : (
          <>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-sm font-bold text-red-400">{critical}</span>
              <span className="text-xs text-gray-500">CRITICAL</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-orange-500" />
              <span className="text-sm font-bold text-orange-400">{high}</span>
              <span className="text-xs text-gray-500">HIGH</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold text-white">{total}</span>
              <span className="text-xs text-gray-500">total findings</span>
            </div>
            <div className="ml-auto flex items-center gap-3 text-xs">
              <span className="text-green-400 font-semibold">{pass} pass</span>
              <span className="text-red-400 font-semibold">{fail} fail</span>
              <span className="text-gray-600">{SCANNERS.length} scanners</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
