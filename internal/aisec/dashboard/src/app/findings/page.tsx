"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Navbar from "@/components/Navbar";
import FilterBar from "@/components/FilterBar";
import { Finding } from "@/lib/types";

const SEV_COLORS: Record<string, string> = {
  CRITICAL: "bg-red-900/40 text-red-300 border-red-700",
  HIGH:     "bg-orange-900/40 text-orange-300 border-orange-700",
  MEDIUM:   "bg-yellow-900/40 text-yellow-300 border-yellow-700",
  LOW:      "bg-blue-900/40 text-blue-300 border-blue-700",
  INFO:     "bg-gray-800 text-gray-400 border-gray-700",
};

const STATUS_COLORS: Record<string, string> = {
  open:           "text-white",
  triaged:        "text-blue-400",
  accepted_risk:  "text-yellow-400",
  fixed:          "text-green-400",
  false_positive: "text-gray-500",
};

function FindingsContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(params.get("search") ?? "");
  const [severity, setSeverity] = useState(params.get("severity") ?? "");
  const [scanner, setScanner] = useState(params.get("scanner") ?? "");
  const [status, setStatus] = useState(params.get("status") ?? "");
  const [scanners, setScanners] = useState<string[]>([]);

  useEffect(() => {
    setLoading(true);
    const q = new URLSearchParams();
    if (search)   q.set("search", search);
    if (severity) q.set("severity", severity);
    if (scanner)  q.set("scanner", scanner);
    if (status)   q.set("status", status);
    fetch(`/api/findings?${q}`, { cache: "no-store" })
      .then(r => r.json())
      .then(d => {
        setFindings(d.findings ?? []);
        setScanners(Array.from(new Set<string>((d.findings ?? []).map((f: Finding) => f.scanner))));
      })
      .finally(() => setLoading(false));
  }, [search, severity, scanner, status]);

  async function handleTriage(id: string, newStatus: Finding["status"]) {
    await fetch(`/api/findings/${id}/triage`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    setFindings(prev => prev.map(f => f.id === id ? { ...f, status: newStatus } : f));
  }

  async function handleExport(fmt: "csv" | "json") {
    const q = new URLSearchParams();
    if (severity) q.set("severity", severity);
    if (scanner)  q.set("scanner", scanner);
    q.set("format", fmt);
    window.open(`/api/export?${q}`, "_blank");
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-black text-white">Findings</h1>
            <p className="text-gray-400 text-sm mt-1">{findings.length} findings across all scanners</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleExport("csv")} className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold px-3 py-1.5 rounded-lg transition-colors">Export CSV</button>
            <button onClick={() => handleExport("json")} className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold px-3 py-1.5 rounded-lg transition-colors">Export JSON</button>
          </div>
        </div>

        <div className="mb-6">
          <FilterBar
            search={search} severity={severity} scanner={scanner} status={status} scanners={scanners}
            onSearch={setSearch} onSeverity={setSeverity} onScanner={setScanner} onStatus={setStatus}
          />
        </div>

        {loading ? (
          <div className="text-gray-500 text-sm">Loading findings…</div>
        ) : findings.length === 0 ? (
          <div className="text-gray-500 text-sm">No findings match the current filters.</div>
        ) : (
          <div className="space-y-2">
            {findings.map(f => (
              <div key={f.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-start gap-4 hover:border-gray-700 transition-colors">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full border shrink-0 ${SEV_COLORS[f.severity] ?? SEV_COLORS.INFO}`}>{f.severity}</span>
                <div className="flex-1 min-w-0">
                  <button onClick={() => router.push(`/findings/${f.id}`)} className="text-white font-semibold text-sm text-left hover:text-teal-400 transition-colors line-clamp-1">
                    {f.title}
                  </button>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    <span className="text-gray-500 text-xs font-mono">{f.scanner}</span>
                    {f.file && <span className="text-gray-600 text-xs font-mono truncate max-w-48">{f.file}{f.line ? `:${f.line}` : ""}</span>}
                    {f.cwe?.map(c => <span key={c} className="text-xs text-purple-400 font-mono">{c}</span>)}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`text-xs font-semibold ${STATUS_COLORS[f.status] ?? "text-white"}`}>{f.status}</span>
                  <select
                    value={f.status}
                    onChange={e => handleTriage(f.id, e.target.value as Finding["status"])}
                    className="text-xs bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-white focus:outline-none"
                  >
                    <option value="open">open</option>
                    <option value="triaged">triaged</option>
                    <option value="accepted_risk">accepted risk</option>
                    <option value="fixed">fixed</option>
                    <option value="false_positive">false positive</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default function FindingsPage() {
  return <Suspense fallback={<div className="min-h-screen bg-gray-950" />}><FindingsContent /></Suspense>;
}
