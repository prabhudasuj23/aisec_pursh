"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import RemediationCard from "@/components/RemediationCard";
import { Finding } from "@/lib/types";
import { enrichCwe } from "@/lib/mappings";

export default function FindingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [finding, setFinding] = useState<Finding | null>(null);
  const [remediation, setRemediation] = useState<string | null>(null);
  const [triageStatus, setTriageStatus] = useState<Finding["status"]>("open");
  const [triageNote, setTriageNote] = useState("");

  useEffect(() => {
    fetch(`/api/findings/${id}`, { cache: "no-store" })
      .then(r => r.json())
      .then(d => {
        setFinding(d.finding);
        setTriageStatus(d.finding?.status ?? "open");
        const cwe = d.finding?.cwe?.[0];
        if (cwe) {
          fetch(`/api/remediation/${encodeURIComponent(cwe)}`)
            .then(r => r.json())
            .then(r => setRemediation(r.content ?? null))
            .catch(() => {});
        }
      });
  }, [id]);

  async function handleTriage() {
    await fetch(`/api/findings/${id}/triage`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: triageStatus, note: triageNote }),
    });
    router.back();
  }

  if (!finding) return <div className="min-h-screen bg-gray-950"><Navbar /></div>;

  const mapping = enrichCwe(finding.cwe ?? []);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <button onClick={() => router.back()} className="text-gray-400 hover:text-white text-sm transition-colors">← Back</button>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-xl font-black text-white">{finding.title}</h1>
            <span className={`text-xs font-bold px-3 py-1 rounded-full border shrink-0 ${
              finding.severity === "CRITICAL" ? "bg-red-900/40 text-red-300 border-red-700" :
              finding.severity === "HIGH"     ? "bg-orange-900/40 text-orange-300 border-orange-700" :
              finding.severity === "MEDIUM"   ? "bg-yellow-900/40 text-yellow-300 border-yellow-700" :
              "bg-blue-900/40 text-blue-300 border-blue-700"
            }`}>{finding.severity}</span>
          </div>

          <p className="text-gray-300 text-sm">{finding.description}</p>

          {finding.file && (
            <div className="bg-gray-950 rounded-xl px-4 py-2.5 font-mono text-sm text-teal-300">
              {finding.file}{finding.line ? `:${finding.line}` : ""}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {mapping.owasp && <span className="text-xs font-bold px-2 py-0.5 rounded-full border bg-purple-900/40 text-purple-300 border-purple-700">{mapping.owasp}</span>}
            {mapping.hipaa?.map(h => <span key={h} className="text-xs font-bold px-2 py-0.5 rounded-full border bg-blue-900/40 text-blue-300 border-blue-700">{h}</span>)}
            {mapping.gdpr?.map(g => <span key={g} className="text-xs font-bold px-2 py-0.5 rounded-full border bg-green-900/40 text-green-300 border-green-700">{g}</span>)}
            {mapping.asvs?.map(a => <span key={a} className="text-xs font-bold px-2 py-0.5 rounded-full border bg-gray-800 text-gray-400 border-gray-700">{a}</span>)}
          </div>
        </div>

        {remediation && <RemediationCard cwe={finding.cwe?.[0] ?? ""} content={remediation} />}

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-white font-black text-sm">Triage</h2>
          <select value={triageStatus} onChange={e => setTriageStatus(e.target.value as Finding["status"])}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500">
            <option value="open">open</option>
            <option value="triaged">triaged</option>
            <option value="accepted_risk">accepted risk</option>
            <option value="fixed">fixed</option>
            <option value="false_positive">false positive</option>
          </select>
          <textarea value={triageNote} onChange={e => setTriageNote(e.target.value)}
            placeholder="Add a triage note…"
            className="w-full bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-teal-500 resize-none h-20" />
          <button onClick={handleTriage} className="bg-teal-600 hover:bg-teal-500 text-white text-sm font-bold px-4 py-2 rounded-xl transition-colors">Save Triage</button>
        </div>
      </main>
    </div>
  );
}
