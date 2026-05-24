"use client";
import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import PostureBar from "@/components/PostureBar";
import ScannerCard from "@/components/ScannerCard";
import { SCANNERS, ScannerCategory, CATEGORY_COLORS } from "@/lib/scanners";

const ALL_CATS: ("All" | ScannerCategory)[] = [
  "All", "SAST", "DAST", "SCA", "Secrets", "IaC", "Container",
  "SBOM", "Vulnerability", "CloudSec", "Network", "AI Security",
];

export interface ScannerStatus {
  status: "pass" | "warn" | "fail" | "no_data" | "runner_offline" | "parse_error";
  counts?: Record<string, number>;
  scanned_at?: string;
}

export default function HomePage() {
  const [cat, setCat] = useState<"All" | ScannerCategory>("All");
  const [statuses, setStatuses] = useState<Record<string, ScannerStatus>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // ONE fetch for all 28 scanners instead of 56 individual requests
    fetch("/api/scanners-status")
      .then(r => r.json())
      .then(d => setStatuses(d.scanners ?? {}))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const visible = cat === "All" ? SCANNERS : SCANNERS.filter(s => s.category === cat);

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <PostureBar statuses={statuses} loading={loading} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        <div>
          <h1 className="text-3xl font-black text-white mb-1">Security Scanners</h1>
          <p className="text-gray-400 text-sm">
            Enterprise DevSecOps scanning platform — all scanners target the{" "}
            <span className="text-teal-400 font-semibold">Pursh</span> telehealth app.
            <span className="text-gray-600 ml-2">{SCANNERS.length} scanners across {ALL_CATS.length - 1} categories</span>
          </p>
        </div>

        {/* Category filter tabs */}
        <div className="flex flex-wrap gap-2">
          {ALL_CATS.map(c => {
            const count = c === "All" ? SCANNERS.length : SCANNERS.filter(s => s.category === c).length;
            const isActive = cat === c;
            return (
              <button
                key={c}
                onClick={() => setCat(c)}
                className={`text-xs font-semibold px-3 py-1.5 rounded-full border transition-all ${
                  isActive
                    ? "bg-teal-700 border-teal-600 text-white shadow-md scale-105"
                    : c === "All"
                      ? "bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700 hover:text-white"
                      : `${CATEGORY_COLORS[c as ScannerCategory]} opacity-75 hover:opacity-100`
                }`}
              >
                {c}
                <span className={`ml-1.5 ${isActive ? "opacity-80" : "opacity-50"}`}>{count}</span>
              </button>
            );
          })}
        </div>

        {cat !== "All" && (
          <p className="text-gray-500 text-xs -mt-2">
            Showing {visible.length} scanner{visible.length !== 1 ? "s" : ""} in <span className="text-white">{cat}</span>
          </p>
        )}

        {/* Scanner grid — status passed as prop, no individual fetches */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {visible.map(scanner => (
            <ScannerCard
              key={scanner.id}
              scanner={scanner}
              result={statuses[scanner.id] ?? null}
              loading={loading}
            />
          ))}
        </div>

      </main>
    </div>
  );
}
