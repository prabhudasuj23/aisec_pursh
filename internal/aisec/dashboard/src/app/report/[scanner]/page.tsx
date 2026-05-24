"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { Finding } from "@/lib/types";
import { SCANNERS, CATEGORY_COLORS } from "@/lib/scanners";

// All 18 runner-backed scanners
const RUNNER_SCANNERS = new Set([
  "semgrep","trivy-sca","trivy-image","gitleaks","grype","checkov","syft","zap",
  "nikto","schemathesis","trufflehog","dependency-check","kics","nuclei","nmap",
  "openvas","suricata","zeek",
]);

const SEV_COLORS: Record<string, string> = {
  CRITICAL: "bg-red-900/40 text-red-300 border-red-700",
  HIGH:     "bg-orange-900/40 text-orange-300 border-orange-700",
  MEDIUM:   "bg-yellow-900/40 text-yellow-300 border-yellow-700",
  LOW:      "bg-blue-900/40 text-blue-300 border-blue-700",
  INFO:     "bg-gray-800 text-gray-400 border-gray-700",
};

const SEV_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

const GRADE_COLORS: Record<string, string> = {
  "A+": "text-emerald-400", A: "text-green-400", B: "text-yellow-400",
  C: "text-orange-400", D: "text-red-400", F: "text-red-600",
};

type ScanStatus = "loading" | "no_data" | "runner_offline" | "planned" | "parse_error" | "pass" | "warn" | "fail";

interface ScanMeta { label?: string; files_scanned?: number; components?: number; passed?: number; failed?: number; targets?: string[]; [key: string]: unknown; }

interface RiskScore { score: number; grade: string; trend: "better" | "worse" | "stable"; change: number; prev_score: number | null; }

interface ComplianceImpact { owasp: Record<string, number>; hipaa: number; pci_dss: number; soc2: number; nist_csf: number; iso27001: number; }

interface Delta { new: number; fixed: number; unchanged: number; new_critical: number; is_first_scan: boolean; }

interface FixEffort { label: string; minutes: number; }

interface ScanResult {
  status: ScanStatus;
  counts?: Record<string, number>;
  findings?: (Finding & { fix_effort?: FixEffort })[];
  scanned_at?: string;
  scan_meta?: ScanMeta;
  risk_score?: RiskScore;
  compliance?: ComplianceImpact;
  delta?: Delta;
  raw?: unknown;
}

interface IntelResult {
  status: string;
  cached?: boolean;
  summary?: string;
  attack_paths?: { title: string; steps: string[]; impact: string; severity: string }[];
  remediation_plan?: { week1?: string[]; week2?: string[]; week3?: string[] };
  exploitability?: string;
  top_priority?: string;
  risk_score?: RiskScore;
  compliance?: ComplianceImpact;
  delta?: Delta;
}

function fmtDate(iso?: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function downloadBlob(data: string, filename: string, mime: string) {
  const blob = new Blob([data], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function toCSV(findings: Finding[]): string {
  const headers = ["severity", "rule_id", "title", "file", "line", "cwe", "remediation", "status"];
  const rows = findings.map(f => headers.map(h => {
    const v = (f as unknown as Record<string, unknown>)[h];
    const s = Array.isArray(v) ? v.join("; ") : String(v ?? "");
    return `"${s.replace(/"/g, '""')}"`;
  }).join(","));
  return [headers.join(","), ...rows].join("\n");
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function RiskScoreCard({ risk, counts }: { risk: RiskScore; counts: Record<string, number> }) {
  const trendIcon = risk.trend === "worse" ? "↑" : risk.trend === "better" ? "↓" : "→";
  const trendColor = risk.trend === "worse" ? "text-red-400" : risk.trend === "better" ? "text-green-400" : "text-gray-400";
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-bold text-sm uppercase tracking-wide">Executive Risk Score</h2>
        <span className="text-xs text-gray-500">0 = no risk · 100 = critical</span>
      </div>
      <div className="flex items-end gap-6">
        <div className="flex items-baseline gap-2">
          <span className="text-6xl font-black text-white">{risk.score}</span>
          <span className="text-gray-500 text-lg font-semibold">/100</span>
        </div>
        <div className="space-y-0.5 pb-1">
          <div className={`text-4xl font-black ${GRADE_COLORS[risk.grade] ?? "text-gray-400"}`}>{risk.grade}</div>
          {risk.prev_score !== null && (
            <div className={`text-sm font-semibold ${trendColor}`}>
              {trendIcon} {risk.change > 0 ? "+" : ""}{risk.change} vs last scan ({risk.prev_score})
            </div>
          )}
          {risk.prev_score === null && <div className="text-xs text-gray-600">First scan — no baseline</div>}
        </div>
      </div>
      {/* Score bar */}
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            risk.score >= 70 ? "bg-red-500" : risk.score >= 45 ? "bg-orange-500" : risk.score >= 20 ? "bg-yellow-500" : "bg-green-500"
          }`}
          style={{ width: `${risk.score}%` }}
        />
      </div>
      <div className="grid grid-cols-5 gap-2 text-center">
        {SEV_ORDER.map(sev => (
          <div key={sev}>
            <div className="text-xl font-black text-white">{counts[sev] ?? 0}</div>
            <div className="text-xs text-gray-500">{sev}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DeltaCard({ delta }: { delta: Delta }) {
  if (delta.is_first_scan) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <h2 className="text-white font-bold text-sm uppercase tracking-wide mb-3">New vs Fixed Findings</h2>
        <p className="text-gray-500 text-sm">First scan — no previous baseline to compare against.</p>
        <p className="text-gray-600 text-xs mt-1">Run the scanner again after fixing issues to see the delta.</p>
      </div>
    );
  }
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
      <h2 className="text-white font-bold text-sm uppercase tracking-wide">New vs Fixed Findings</h2>
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-red-900/20 border border-red-800/40 rounded-xl p-3 text-center">
          <div className="text-2xl font-black text-red-400">{delta.new}</div>
          <div className="text-xs text-gray-400 mt-0.5">NEW</div>
          {delta.new_critical > 0 && (
            <div className="text-xs text-red-500 font-semibold mt-0.5">{delta.new_critical} critical</div>
          )}
        </div>
        <div className="bg-green-900/20 border border-green-800/40 rounded-xl p-3 text-center">
          <div className="text-2xl font-black text-green-400">{delta.fixed}</div>
          <div className="text-xs text-gray-400 mt-0.5">FIXED</div>
        </div>
        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-3 text-center">
          <div className="text-2xl font-black text-gray-300">{delta.unchanged}</div>
          <div className="text-xs text-gray-400 mt-0.5">UNCHANGED</div>
        </div>
      </div>
    </div>
  );
}

function ComplianceCard({ compliance }: { compliance: ComplianceImpact }) {
  const owaspTotal = Object.values(compliance.owasp).reduce((a, b) => a + b, 0);
  const frameworks = [
    { label: "OWASP Top 10", count: owaspTotal, color: "text-orange-400" },
    { label: "HIPAA", count: compliance.hipaa, color: "text-blue-400" },
    { label: "PCI-DSS", count: compliance.pci_dss, color: "text-purple-400" },
    { label: "SOC 2", count: compliance.soc2, color: "text-teal-400" },
    { label: "NIST CSF", count: compliance.nist_csf, color: "text-green-400" },
    { label: "ISO 27001", count: compliance.iso27001, color: "text-yellow-400" },
  ];
  const topOwasp = Object.entries(compliance.owasp).sort(([, a], [, b]) => b - a).slice(0, 3);
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <h2 className="text-white font-bold text-sm uppercase tracking-wide">Compliance Impact</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {frameworks.map(fw => (
          <div key={fw.label} className="bg-gray-800/60 rounded-xl p-3">
            <div className={`text-xl font-black ${fw.count > 0 ? fw.color : "text-gray-600"}`}>{fw.count}</div>
            <div className="text-xs text-gray-400 mt-0.5">{fw.label}</div>
            <div className="text-xs text-gray-600">{fw.count === 0 ? "Clean" : "violation" + (fw.count > 1 ? "s" : "")}</div>
          </div>
        ))}
      </div>
      {topOwasp.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Top OWASP Categories</p>
          <div className="space-y-1.5">
            {topOwasp.map(([cat, count]) => (
              <div key={cat} className="flex items-center justify-between">
                <span className="text-orange-300 text-xs">{cat}</span>
                <span className="text-white text-xs font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function AiIntelPanel({ scannerId }: { scannerId: string }) {
  const [intel, setIntel] = useState<IntelResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"summary" | "paths" | "plan">("summary");

  async function runAnalysis() {
    setLoading(true);
    try {
      const res = await fetch(`/api/intelligence/${scannerId}`, { cache: "no-store" });
      const data = await res.json();
      setIntel(data);
    } catch {
      setIntel({ status: "runner_offline" });
    } finally {
      setLoading(false);
    }
  }

  const explColor = intel?.exploitability === "High" ? "text-red-400" : intel?.exploitability === "Medium" ? "text-orange-400" : "text-green-400";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-white font-bold text-sm uppercase tracking-wide flex items-center gap-2">
            <span className="text-pink-400">✦</span> AI Security Intelligence
            <span className="text-xs font-normal text-gray-500 ml-1">powered by DeepSeek</span>
          </h2>
          {intel?.cached && <span className="text-xs text-gray-600">Cached result</span>}
        </div>
        {!intel && (
          <button
            onClick={runAnalysis}
            disabled={loading}
            className="text-xs bg-pink-900/40 hover:bg-pink-800/60 border border-pink-700/60 text-pink-300 font-semibold px-4 py-1.5 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Analyzing…" : "Run AI Analysis"}
          </button>
        )}
        {intel && (
          <button
            onClick={runAnalysis}
            disabled={loading}
            className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-400 font-semibold px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Re-analyzing…" : "Refresh"}
          </button>
        )}
      </div>

      {!intel && !loading && (
        <p className="text-gray-500 text-sm">
          Click <span className="text-pink-300 font-semibold">Run AI Analysis</span> to get an executive summary,
          top attack paths, and a prioritized remediation plan — generated by DeepSeek from the actual scan findings.
        </p>
      )}

      {loading && (
        <div className="space-y-2 animate-pulse">
          <div className="h-3 bg-gray-800 rounded w-3/4" />
          <div className="h-3 bg-gray-800 rounded w-1/2" />
          <div className="h-3 bg-gray-800 rounded w-2/3" />
        </div>
      )}

      {intel && intel.status !== "ok" && (
        <p className="text-red-400 text-sm">Analysis failed — runner may be offline or DEEPSEEK_API_KEY not set.</p>
      )}

      {intel && intel.status === "ok" && (
        <>
          {/* Exploitability + top priority */}
          <div className="flex items-center gap-4 bg-gray-800/60 rounded-xl px-4 py-3">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Exploitability</p>
              <p className={`text-lg font-black ${explColor}`}>{intel.exploitability}</p>
            </div>
            {intel.top_priority && (
              <div className="flex-1 border-l border-gray-700 pl-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">Priority Action</p>
                <p className="text-teal-300 text-sm font-semibold">{intel.top_priority}</p>
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-1">
            {(["summary", "paths", "plan"] as const).map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors capitalize ${
                  activeTab === tab ? "bg-pink-900/50 text-pink-300 border border-pink-700/50" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}>
                {tab === "paths" ? "Attack Paths" : tab === "plan" ? "Remediation Plan" : "Summary"}
              </button>
            ))}
          </div>

          {activeTab === "summary" && intel.summary && (
            <div className="bg-gray-800/40 rounded-xl p-4">
              <p className="text-gray-200 text-sm leading-relaxed">{intel.summary}</p>
            </div>
          )}

          {activeTab === "paths" && (
            <div className="space-y-3">
              {(intel.attack_paths ?? []).length === 0 ? (
                <p className="text-gray-500 text-sm">No significant attack paths identified.</p>
              ) : (intel.attack_paths ?? []).map((ap, i) => (
                <div key={i} className="bg-gray-800/40 rounded-xl p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border shrink-0 ${SEV_COLORS[ap.severity] ?? SEV_COLORS.INFO}`}>{ap.severity}</span>
                    <p className="text-white font-semibold text-sm">{ap.title}</p>
                  </div>
                  <ol className="space-y-1 pl-2">
                    {ap.steps.map((step, j) => (
                      <li key={j} className="text-gray-400 text-xs flex gap-2">
                        <span className="text-gray-600 shrink-0">{j + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                  {ap.impact && (
                    <div className="border-t border-gray-700 pt-2">
                      <span className="text-xs text-gray-500 uppercase tracking-wide">Impact: </span>
                      <span className="text-red-300 text-xs">{ap.impact}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {activeTab === "plan" && intel.remediation_plan && (
            <div className="space-y-3">
              {(["week1", "week2", "week3"] as const).map((week, i) => {
                const items = intel.remediation_plan?.[week] ?? [];
                if (items.length === 0) return null;
                return (
                  <div key={week} className="bg-gray-800/40 rounded-xl p-4 space-y-2">
                    <p className="text-white font-bold text-sm">Week {i + 1}</p>
                    <ul className="space-y-1.5">
                      {items.map((item, j) => (
                        <li key={j} className="flex items-start gap-2 text-gray-300 text-sm">
                          <span className="text-teal-500 shrink-0 mt-0.5">✓</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ReportPage() {
  const { scanner: scannerId } = useParams<{ scanner: string }>();
  const router = useRouter();
  const [result, setResult] = useState<ScanResult>({ status: "loading" });
  const [sevFilter, setSevFilter] = useState<string>("ALL");
  const [copied, setCopied] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const scannerDef = SCANNERS.find(s => s.id === scannerId);

  const fetchResult = useCallback(async () => {
    if (!RUNNER_SCANNERS.has(scannerId)) {
      setResult({ status: "planned" });
      return;
    }
    setResult({ status: "loading" });
    try {
      const res = await fetch(`/api/results/${scannerId}`, { cache: "no-store" });
      const data = await res.json();
      setResult(data as ScanResult);
    } catch {
      setResult({ status: "runner_offline" });
    }
  }, [scannerId]);

  useEffect(() => { fetchResult(); }, [fetchResult]);

  const findings = result.findings ?? [];
  const filtered = sevFilter === "ALL" ? findings : findings.filter(f => f.severity === sevFilter);
  const counts = result.counts ?? {};
  const totalFindings = findings.length;

  function handleCopy() {
    navigator.clipboard.writeText(JSON.stringify(findings, null, 2));
    setCopied(true); setTimeout(() => setCopied(false), 2000);
  }
  function handleExportJSON() { downloadBlob(JSON.stringify(findings, null, 2), `${scannerId}-findings.json`, "application/json"); }
  function handleExportCSV() { downloadBlob(toCSV(findings), `${scannerId}-findings.csv`, "text/csv"); }

  const statusBadge = (s: ScanStatus) => {
    if (s === "fail")    return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-red-900/40 text-red-300 border border-red-700">FAIL</span>;
    if (s === "warn")    return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-orange-900/40 text-orange-300 border border-orange-700">WARN</span>;
    if (s === "pass")    return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-900/40 text-green-300 border border-green-700">PASS</span>;
    if (s === "no_data") return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700">NO DATA</span>;
    return null;
  };

  const hasResults = result.status === "pass" || result.status === "warn" || result.status === "fail";

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <button onClick={() => router.back()} className="text-gray-400 hover:text-white text-sm transition-colors shrink-0">
                ← Back
              </button>
              <h1 className="text-2xl font-black text-white">{scannerDef?.label ?? scannerId}</h1>
              {scannerDef && (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${CATEGORY_COLORS[scannerDef.category]}`}>
                  {scannerDef.category}
                </span>
              )}
              {result.status !== "loading" && statusBadge(result.status)}
            </div>
            {scannerDef && <p className="text-gray-400 text-sm">{scannerDef.description}</p>}
            <div className="flex items-center gap-4 text-xs text-gray-500">
              {result.scanned_at && <span>Last scan: {fmtDate(result.scanned_at)}</span>}
              {result.scanned_at && <span>·</span>}
              {scannerDef && (
                <a href={scannerDef.ghWorkflow} target="_blank" rel="noreferrer"
                  className="text-teal-500 hover:text-teal-400 transition-colors">
                  View CI workflow ↗
                </a>
              )}
            </div>
          </div>
          {totalFindings > 0 && (
            <div className="flex gap-2 shrink-0">
              <button onClick={handleCopy} className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold px-3 py-1.5 rounded-lg transition-colors">
                {copied ? "✓ Copied" : "Copy JSON"}
              </button>
              <button onClick={handleExportJSON} className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold px-3 py-1.5 rounded-lg transition-colors">
                Export JSON
              </button>
              <button onClick={handleExportCSV} className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold px-3 py-1.5 rounded-lg transition-colors">
                Export CSV
              </button>
            </div>
          )}
        </div>

        {/* ── Empty / error states ─────────────────────────────────────────────── */}
        {result.status === "loading" && <div className="text-gray-500 text-sm animate-pulse">Loading scan results…</div>}

        {result.status === "planned" && (
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 text-center space-y-3">
            <div className="text-4xl">🔜</div>
            <h2 className="text-white font-bold text-lg">Scanner not yet configured</h2>
            <p className="text-gray-400 text-sm max-w-md mx-auto">
              {scannerDef?.label ?? scannerId} is planned for a future phase. The runner integration and result files are not yet built.
            </p>
          </div>
        )}

        {result.status === "runner_offline" && (
          <div className="bg-gray-900 border border-red-900/40 rounded-2xl p-6 space-y-2">
            <h2 className="text-red-400 font-bold">Runner offline</h2>
            <p className="text-gray-400 text-sm">The AISec runner (port 8002) is not reachable. Start it with:</p>
            <pre className="text-xs bg-gray-950 rounded-lg p-3 text-teal-300 font-mono overflow-x-auto">
              cd internal/aisec/runner{"\n"}uvicorn main:app --port 8002 --reload
            </pre>
          </div>
        )}

        {result.status === "parse_error" && (
          <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-2xl p-4">
            <p className="text-yellow-400 text-sm font-semibold">Result file exists but could not be parsed. Re-run the scanner.</p>
          </div>
        )}

        {result.status === "no_data" && (
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 text-center space-y-3">
            <div className="text-4xl">📭</div>
            <h2 className="text-white font-bold text-lg">No scan data yet</h2>
            <p className="text-gray-400 text-sm">Run the scanner from the Scanners page to generate results.</p>
            <button onClick={() => router.push("/scanners")}
              className="mt-2 text-xs bg-teal-700 hover:bg-teal-600 text-white font-bold px-4 py-2 rounded-lg transition-colors">
              Go to Scanners
            </button>
          </div>
        )}

        {/* ── Results ──────────────────────────────────────────────────────────── */}
        {hasResults && (
          <>
            {/* Scan coverage banner */}
            {result.scan_meta?.label && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 flex items-center gap-3">
                <span className="text-lg">🔍</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-semibold">{result.scan_meta.label}</p>
                  {result.scan_meta.targets && result.scan_meta.targets.length > 0 && (
                    <p className="text-gray-500 text-xs font-mono mt-0.5 truncate">{result.scan_meta.targets.join(", ")}</p>
                  )}
                  {result.scan_meta.passed !== undefined && (
                    <p className="text-xs mt-0.5">
                      <span className="text-green-400 font-semibold">{result.scan_meta.passed} passed</span>
                      {result.scan_meta.failed !== undefined && (
                        <span className="text-red-400 font-semibold"> · {result.scan_meta.failed} failed</span>
                      )}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Row 1: Risk Score + Delta */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {result.risk_score && <RiskScoreCard risk={result.risk_score} counts={counts} />}
              {result.delta && <DeltaCard delta={result.delta} />}
            </div>

            {/* Row 2: Compliance Impact */}
            {result.compliance && <ComplianceCard compliance={result.compliance} />}

            {/* Row 3: AI Intelligence Panel */}
            <AiIntelPanel scannerId={scannerId} />

            {/* Row 4: Findings */}
            {totalFindings === 0 ? (
              <div className="flex items-center gap-3 bg-green-900/20 border border-green-700/40 rounded-2xl p-4">
                <span className="text-2xl">✅</span>
                <div>
                  <p className="text-green-400 font-bold">No findings — scan passed cleanly</p>
                  <p className="text-gray-400 text-sm mt-0.5">The scanner completed without detecting any issues.</p>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-gray-400 text-sm font-semibold">
                    {filtered.length} of {totalFindings} findings
                  </span>
                  <div className="flex gap-1 ml-auto">
                    {["ALL", ...SEV_ORDER].map(s => (
                      <button key={s} onClick={() => setSevFilter(s)}
                        className={`text-xs font-semibold px-2.5 py-1 rounded-lg transition-colors ${
                          sevFilter === s ? "bg-teal-700 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                        }`}>
                        {s}
                        {s !== "ALL" && counts[s] !== undefined && (
                          <span className="ml-1 opacity-60">{counts[s]}</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  {filtered.map(f => (
                    <div key={f.id} className="bg-gray-900 border border-gray-800 hover:border-gray-700 rounded-xl transition-colors">
                      <button className="w-full flex items-start gap-3 p-4 text-left"
                        onClick={() => setExpandedId(prev => prev === f.id ? null : f.id)}>
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full border shrink-0 mt-0.5 ${SEV_COLORS[f.severity] ?? SEV_COLORS.INFO}`}>
                          {f.severity}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-white font-semibold text-sm line-clamp-1">{f.title}</p>
                          <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                            {f.rule_id && <span className="text-gray-500 text-xs font-mono">{f.rule_id}</span>}
                            {f.file && (
                              <span className="text-gray-600 text-xs font-mono truncate max-w-xs">
                                {f.file}{f.line ? `:${f.line}` : ""}
                              </span>
                            )}
                            {f.cwe?.map(c => (
                              <span key={c} className="text-xs text-purple-400 font-mono">{c}</span>
                            ))}
                          </div>
                        </div>
                        {/* Fix effort pill */}
                        {(f as unknown as { fix_effort?: FixEffort }).fix_effort && (
                          <span className="text-xs text-gray-500 shrink-0 hidden sm:block mt-0.5">
                            ⏱ {(f as unknown as { fix_effort: FixEffort }).fix_effort.label}
                          </span>
                        )}
                        <span className="text-gray-600 text-xs shrink-0">{expandedId === f.id ? "▲" : "▼"}</span>
                      </button>

                      {expandedId === f.id && (
                        <div className="border-t border-gray-800 px-4 py-4 space-y-4">
                          {f.description && f.description !== f.title && (
                            <div>
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Description</p>
                              <p className="text-gray-300 text-sm leading-relaxed">{f.description}</p>
                            </div>
                          )}
                          {f.remediation && (
                            <div>
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Remediation</p>
                              <p className="text-teal-300 text-sm leading-relaxed">{f.remediation}</p>
                            </div>
                          )}
                          <div className="grid grid-cols-2 gap-3 text-xs">
                            {f.file && (
                              <div>
                                <p className="text-gray-500 uppercase tracking-wide mb-0.5">Location</p>
                                <p className="text-gray-300 font-mono break-all">{f.file}{f.line ? `:${f.line}` : ""}</p>
                              </div>
                            )}
                            {f.rule_id && (
                              <div>
                                <p className="text-gray-500 uppercase tracking-wide mb-0.5">Rule ID</p>
                                <p className="text-gray-300 font-mono">{f.rule_id}</p>
                              </div>
                            )}
                            {(f as unknown as { fix_effort?: FixEffort }).fix_effort && (
                              <div>
                                <p className="text-gray-500 uppercase tracking-wide mb-0.5">Fix Effort</p>
                                <p className="text-yellow-400 font-semibold">
                                  {(f as unknown as { fix_effort: FixEffort }).fix_effort.label}
                                </p>
                              </div>
                            )}
                            {f.cwe && f.cwe.length > 0 && (
                              <div>
                                <p className="text-gray-500 uppercase tracking-wide mb-0.5">CWE</p>
                                <div className="flex flex-wrap gap-1">
                                  {f.cwe.map(c => (
                                    <a key={c}
                                      href={`https://cwe.mitre.org/data/definitions/${c.replace("CWE-", "")}.html`}
                                      target="_blank" rel="noreferrer"
                                      className="text-purple-400 hover:text-purple-300 font-mono transition-colors">
                                      {c} ↗
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}
                            {f.owasp_top10 && (
                              <div>
                                <p className="text-gray-500 uppercase tracking-wide mb-0.5">OWASP Top 10</p>
                                <p className="text-orange-400 font-semibold">{f.owasp_top10}</p>
                              </div>
                            )}
                            {f.hipaa && f.hipaa.length > 0 && (
                              <div>
                                <p className="text-gray-500 uppercase tracking-wide mb-0.5">HIPAA</p>
                                <p className="text-blue-400 font-mono">{f.hipaa.join(", ")}</p>
                              </div>
                            )}
                            {f.gdpr && f.gdpr.length > 0 && (
                              <div>
                                <p className="text-gray-500 uppercase tracking-wide mb-0.5">GDPR Art. 32</p>
                                <p className="text-green-400 font-mono">{f.gdpr.join(", ")}</p>
                              </div>
                            )}
                          </div>
                          {f.scanned_at && <p className="text-gray-600 text-xs">Scanned: {fmtDate(f.scanned_at)}</p>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
