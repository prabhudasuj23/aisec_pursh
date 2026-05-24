"use client";
import { useEffect, useState, useRef } from "react";
import { createClient } from "@/lib/supabase";

interface RunEntry {
  run_id: string;
  scanner_id: string;
  scanner_name?: string;
  started_at: string;
  finished_at?: string;
  exit_code?: number;
  status: string;
  counts: Record<string, number>;
  findings_count: number;
  risk_score?: { score: number; grade: string; trend: string };
  image_tag?: string;
}

interface Props { scannerId: string; refreshTrigger: number; }

const SEV_COLORS: Record<string, string> = {
  CRITICAL: "bg-red-900/40 text-red-300",
  HIGH:     "bg-orange-900/40 text-orange-300",
  MEDIUM:   "bg-yellow-900/40 text-yellow-300",
  LOW:      "bg-blue-900/40 text-blue-300",
};

const GRADE_COLOR: Record<string, string> = {
  "A+": "text-emerald-400", A: "text-green-400", B: "text-yellow-400",
  C: "text-orange-400", D: "text-red-400", F: "text-red-600",
};

function relativeTime(iso: string): string {
  try {
    // Supabase returns ISO strings with offset (+00:00) — don't append Z
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  } catch { return "—"; }
}

function statusIcon(run: RunEntry): { icon: string; color: string; label: string } {
  if (run.status === "running") return { icon: "⟳", color: "text-blue-400 animate-spin", label: "Running" };
  if (run.status === "failed")  return { icon: "✕", color: "text-red-400",    label: "Failed" };
  if (run.findings_count === 0) return { icon: "✓", color: "text-green-400",  label: "Clean" };
  return { icon: "⚠", color: "text-yellow-400", label: "Findings" };
}

export default function RunHistoryPanel({ scannerId, refreshTrigger }: Props) {
  const [history, setHistory] = useState<RunEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();
  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);

  async function fetchHistory() {
    setLoading(true);
    try {
      // Fetch directly from Supabase — authenticated via session cookie
      const { data, error } = await supabase
        .from("scan_runs")
        .select(
          "run_id, scanner_id, scanner_name, started_at, finished_at, " +
          "exit_code, status, counts, findings_count, risk_score"
        )
        .eq("scanner_id", scannerId)
        .order("created_at", { ascending: false })
        .limit(10);

      if (!error && data) {
        setHistory(data as unknown as RunEntry[]);
      }
    } finally {
      setLoading(false);
    }
  }

  // Initial fetch + re-fetch whenever a scan completes (refreshTrigger bumped)
  useEffect(() => {
    fetchHistory();
  }, [scannerId, refreshTrigger]);

  // Supabase Realtime — subscribe to INSERT/UPDATE on scan_runs for this scanner
  // so history updates the instant the runner writes the completed row
  useEffect(() => {
    const channel = supabase
      .channel(`scan_runs:${scannerId}`)
      .on(
        "postgres_changes",
        {
          event: "*",           // INSERT (start_run) + UPDATE (finish_run)
          schema: "public",
          table: "scan_runs",
          filter: `scanner_id=eq.${scannerId}`,
        },
        (_payload) => {
          // Re-fetch on any row change for this scanner
          fetchHistory();
        }
      )
      .subscribe();

    channelRef.current = channel;
    return () => { supabase.removeChannel(channel); };
  }, [scannerId]);

  if (loading && history.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <h2 className="text-white font-black text-sm mb-3">Run History</h2>
        <p className="text-gray-600 text-xs animate-pulse">Loading from Supabase…</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-black text-sm">Run History</h2>
        <span className="text-[10px] text-teal-600 font-mono">Supabase · live</span>
      </div>

      {history.length === 0 ? (
        <p className="text-gray-500 text-sm">No runs yet. Complete pre-checks and run a scan.</p>
      ) : (
        <div className="space-y-2">
          {history.map((run) => {
            const { icon, color, label } = statusIcon(run);
            const grade = run.risk_score?.grade;
            return (
              <div key={run.run_id}
                className="flex items-center gap-3 border-b border-gray-800/60 pb-2 last:border-0 last:pb-0">

                {/* Status icon */}
                <span className={`text-base shrink-0 ${color}`} title={label}>
                  {icon}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap gap-1 mb-1">
                    {(["CRITICAL","HIGH","MEDIUM","LOW"] as const).map(sev =>
                      (run.counts?.[sev] ?? 0) > 0 ? (
                        <span key={sev} className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${SEV_COLORS[sev]}`}>
                          {run.counts[sev]} {sev}
                        </span>
                      ) : null
                    )}
                    {run.findings_count === 0 && run.status !== "running" && (
                      <span className="text-[10px] text-gray-500">No findings</span>
                    )}
                    {run.status === "running" && (
                      <span className="text-[10px] text-blue-400 animate-pulse">Scanning…</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="text-gray-600 text-[10px]" title={run.started_at}>
                      {relativeTime(run.started_at)}
                    </p>
                    {grade && (
                      <span className={`text-[10px] font-black ${GRADE_COLOR[grade] ?? "text-gray-400"}`}>
                        Risk {grade}
                      </span>
                    )}
                    {run.image_tag && (
                      <span className="text-[10px] text-teal-600 font-mono">{run.image_tag}</span>
                    )}
                  </div>
                </div>

                {/* View link */}
                <a href={`/report/${scannerId}`}
                  className="shrink-0 text-xs text-teal-400 hover:text-teal-300 font-semibold transition-colors">
                  View →
                </a>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
