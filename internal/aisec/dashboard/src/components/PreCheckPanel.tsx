"use client";
import { useEffect, useState, useCallback } from "react";
import { PreCheckItem } from "@/lib/types";

interface Props {
  scannerId: string;
  onAllPass: (passed: boolean) => void;
}

export default function PreCheckPanel({ scannerId, onAllPass }: Props) {
  const [checks, setChecks] = useState<PreCheckItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [allPass, setAllPass] = useState(false);

  const runChecks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/precheck/${scannerId}`, { cache: "no-store" });
      const data = await res.json();
      setChecks(data.checks ?? []);
      setAllPass(data.all_pass ?? false);
      onAllPass(data.all_pass ?? false);
    } catch {
      setChecks([{ name: "Runner", status: "fail", message: "Cannot reach runner on port 8002", blocking: true }]);
      setAllPass(false);
      onAllPass(false);
    }
    setLoading(false);
  }, [scannerId, onAllPass]);

  useEffect(() => { runChecks(); }, [runChecks]);

  function icon(status: PreCheckItem["status"]) {
    if (status === "pass") return <span className="text-green-400">✅</span>;
    if (status === "fail") return <span className="text-red-400">❌</span>;
    if (status === "warn") return <span className="text-yellow-400">⚠</span>;
    return <span className="w-4 h-4 border-2 border-gray-500/30 border-t-gray-400 rounded-full animate-spin inline-block" />;
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-black text-sm">Pre-checks</h2>
        <button
          onClick={runChecks}
          disabled={loading}
          className="text-xs text-teal-400 hover:text-teal-300 disabled:opacity-50 font-semibold transition-colors"
        >
          {loading ? "Checking…" : "Re-run checks"}
        </button>
      </div>

      <div className="space-y-2">
        {loading && checks.length === 0 ? (
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <span className="w-4 h-4 border-2 border-gray-500/30 border-t-gray-400 rounded-full animate-spin" />
            Running checks…
          </div>
        ) : (
          checks.map((check, i) => (
            <div key={i} className="flex items-start gap-3">
              <span className="shrink-0 text-sm mt-0.5">{icon(check.status)}</span>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-semibold">{check.name}</p>
                <p className="text-gray-500 text-xs">{check.message}</p>
              </div>
              {check.blocking && check.status === "fail" && (
                <span className="text-[10px] text-red-400 border border-red-700/40 px-1.5 py-0.5 rounded font-bold shrink-0">BLOCKING</span>
              )}
            </div>
          ))
        )}
      </div>

      {!loading && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold ${
          allPass ? "bg-green-900/20 border border-green-700/40 text-green-300" : "bg-red-900/20 border border-red-700/40 text-red-300"
        }`}>
          {allPass ? "✅ All checks passed — ready to scan" : "❌ Fix failing checks to enable scan"}
        </div>
      )}
    </div>
  );
}
