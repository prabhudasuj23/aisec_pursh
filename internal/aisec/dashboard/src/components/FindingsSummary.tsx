"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface Props { scannerId: string; refreshTrigger: number; }

const SEV: { key: string; color: string }[] = [
  { key: "CRITICAL", color: "bg-red-900/40 text-red-300 border-red-700" },
  { key: "HIGH",     color: "bg-orange-900/40 text-orange-300 border-orange-700" },
  { key: "MEDIUM",   color: "bg-yellow-900/40 text-yellow-300 border-yellow-700" },
  { key: "LOW",      color: "bg-blue-900/40 text-blue-300 border-blue-700" },
];

export default function FindingsSummary({ scannerId, refreshTrigger }: Props) {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState<string>("no_data");
  const router = useRouter();

  useEffect(() => {
    fetch(`/api/results/${scannerId}`, { cache: "no-store" })
      .then(r => r.json())
      .then(d => {
        setCounts(d.counts ?? {});
        setTotal(Object.values(d.counts ?? {}).reduce((a: number, b) => a + (b as number), 0));
        setStatus(d.status ?? "no_data");
      })
      .catch(() => setStatus("runner_offline"));
  }, [scannerId, refreshTrigger]);

  if (status === "no_data") return null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-black text-sm">Latest Findings</h2>
        <button onClick={() => router.push(`/findings?scanner=${scannerId}`)} className="text-xs text-teal-400 hover:text-teal-300 font-semibold transition-colors">
          View all →
        </button>
      </div>
      {total === 0 ? (
        <p className="text-green-400 text-sm font-semibold">✅ No findings</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {SEV.map(({ key, color }) =>
            (counts[key] ?? 0) > 0 ? (
              <button key={key} onClick={() => router.push(`/findings?scanner=${scannerId}&severity=${key}`)}
                className={`text-xs font-bold px-3 py-1 rounded-full border hover:opacity-80 transition-opacity ${color}`}>
                {counts[key]} {key}
              </button>
            ) : null
          )}
        </div>
      )}
    </div>
  );
}
