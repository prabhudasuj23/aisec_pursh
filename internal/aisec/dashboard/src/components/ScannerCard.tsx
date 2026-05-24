"use client";
import { useRouter } from "next/navigation";
import { ScannerDef, CATEGORY_COLORS } from "@/lib/scanners";
import type { ScannerStatus } from "@/app/page";

interface Props {
  scanner: ScannerDef;
  result: ScannerStatus | null;
  loading?: boolean;
}

const STATUS_STYLE = {
  pass:          { badge: "bg-green-900/50 text-green-300 border-green-700",   dot: "bg-green-400",           label: "PASS"    },
  warn:          { badge: "bg-yellow-900/50 text-yellow-300 border-yellow-700", dot: "bg-yellow-400",          label: "WARN"    },
  fail:          { badge: "bg-red-900/50 text-red-300 border-red-700",          dot: "bg-red-500 animate-pulse",label: "FAIL"    },
  no_data:       { badge: "bg-gray-800 text-gray-500 border-gray-700",          dot: "bg-gray-600",            label: "NO DATA" },
  runner_offline:{ badge: "bg-gray-800 text-gray-500 border-gray-700",          dot: "bg-gray-600",            label: "OFFLINE" },
  parse_error:   { badge: "bg-gray-800 text-gray-500 border-gray-700",          dot: "bg-gray-600",            label: "ERROR"   },
};

export default function ScannerCard({ scanner, result, loading }: Props) {
  const router = useRouter();

  const s = result?.status ?? "no_data";
  const style = STATUS_STYLE[s] ?? STATUS_STYLE.no_data;
  const counts = result?.counts ?? {};
  const total = Object.values(counts).reduce((a, b) => a + b, 0);

  function fmtTime(iso?: string) {
    if (!iso) return null;
    try { return new Date(iso).toLocaleString(); } catch { return null; }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-4 hover:border-teal-700/50 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${CATEGORY_COLORS[scanner.category]}`}>
              {scanner.category}
            </span>
          </div>
          <h3 className="text-white font-black text-lg leading-tight">{scanner.label}</h3>
          <p className="text-gray-500 text-xs mt-0.5 leading-snug">{scanner.description}</p>
        </div>

        {loading ? (
          <div className="shrink-0 flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full border bg-gray-800 border-gray-700 text-gray-600">
            <span className="w-2 h-2 rounded-full bg-gray-700 animate-pulse" />…
          </div>
        ) : (
          <div className={`shrink-0 flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full border ${style.badge}`}>
            <span className={`w-2 h-2 rounded-full ${style.dot}`} />
            {style.label}
          </div>
        )}
      </div>

      {!loading && total > 0 && (
        <div className="flex gap-2 flex-wrap">
          {["CRITICAL","HIGH","MEDIUM","LOW"].map((sev) =>
            counts[sev] ? (
              <span key={sev} className={`text-xs font-bold px-2 py-0.5 rounded-full border ${
                sev === "CRITICAL" ? "bg-red-900/40 text-red-300 border-red-700" :
                sev === "HIGH"     ? "bg-orange-900/40 text-orange-300 border-orange-700" :
                sev === "MEDIUM"   ? "bg-yellow-900/40 text-yellow-300 border-yellow-700" :
                                     "bg-blue-900/40 text-blue-300 border-blue-700"
              }`}>
                {counts[sev]} {sev}
              </span>
            ) : null
          )}
        </div>
      )}

      {!loading && s === "pass" && total === 0 && (
        <p className="text-green-400 text-xs font-semibold">✅ No findings</p>
      )}

      {!loading && result?.scanned_at && (
        <p className="text-gray-600 text-xs">Last scan: {fmtTime(result.scanned_at)}</p>
      )}

      <div className="flex gap-2 mt-auto">
        <button
          onClick={() => router.push(`/scan/${scanner.id}`)}
          className="flex-1 bg-teal-700 hover:bg-teal-600 text-white text-xs font-bold py-2 rounded-xl transition-colors flex items-center justify-center gap-1.5"
        >
          ▶ Start
        </button>
        <button
          onClick={() => router.push(`/report/${scanner.id}`)}
          className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-bold py-2 rounded-xl transition-colors"
        >
          📋 View Report
        </button>
        <a
          href={scanner.ghWorkflow}
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 bg-gray-800 hover:bg-gray-700 text-gray-400 text-xs font-bold py-2 rounded-xl transition-colors"
          title="GitHub Actions"
        >
          GH ↗
        </a>
      </div>
    </div>
  );
}
