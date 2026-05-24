"use client";
import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import PreCheckPanel from "@/components/PreCheckPanel";
import DockerfilePicker from "@/components/DockerfilePicker";
import RunHistoryPanel from "@/components/RunHistoryPanel";
import ScanTerminal from "@/components/ScanTerminal";
import FindingsSummary from "@/components/FindingsSummary";
import { SCANNERS, CATEGORY_COLORS } from "@/lib/scanners";

export default function ScanWorkspacePage() {
  const { scanner: scannerId } = useParams<{ scanner: string }>();
  const router = useRouter();
  const scannerDef = SCANNERS.find(s => s.id === scannerId);

  const [checksPass, setChecksPass] = useState(false);
  const [builtImageTag, setBuiltImageTag] = useState<string | null>(null);
  const [runKey, setRunKey] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [historyRefresh, setHistoryRefresh] = useState(0);

  const isImageScanner = scannerId === "trivy-image";
  const canScan = checksPass && (!isImageScanner || builtImageTag !== null);

  const handleAllPass = useCallback((passed: boolean) => { setChecksPass(passed); }, []);

  function handleRunScan() { setRunKey(k => k + 1); setIsRunning(true); }
  function handleScanDone(_exitCode: number) { setIsRunning(false); setHistoryRefresh(n => n + 1); }

  if (!scannerDef) {
    return (
      <div className="min-h-screen bg-gray-950 text-white">
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-12 text-center text-gray-500">
          Unknown scanner: {scannerId}.{" "}
          <button onClick={() => router.push("/")} className="text-teal-400 underline">Back to home</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <div className="sticky top-14 z-30 border-b border-gray-800 bg-gray-950/95 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 h-12 flex items-center gap-4">
          <button onClick={() => router.push("/")} className="text-gray-400 hover:text-white text-sm transition-colors">← Scanners</button>
          <span className="text-gray-700">/</span>
          <span className="text-white font-black text-sm">{scannerDef.label}</span>
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${CATEGORY_COLORS[scannerDef.category]}`}>{scannerDef.category}</span>
          <div className="ml-auto">
            <a href={scannerDef.ghWorkflow} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">GitHub Actions ↗</a>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-gray-400 text-sm mb-6">{scannerDef.description}</p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-5">
            <PreCheckPanel scannerId={scannerId} onAllPass={handleAllPass} />
            {isImageScanner && <DockerfilePicker onImageReady={setBuiltImageTag} />}
            <button
              onClick={handleRunScan}
              disabled={!canScan || isRunning}
              className={`w-full py-3 rounded-2xl font-black text-sm transition-all ${
                canScan && !isRunning ? "bg-teal-600 hover:bg-teal-500 text-white shadow-lg shadow-teal-900/30" : "bg-gray-800 text-gray-600 cursor-not-allowed"
              }`}
            >
              {isRunning ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Scanning…
                </span>
              ) : canScan ? "▶ Run Scan"
                : isImageScanner && checksPass && !builtImageTag ? "Build the Docker image first"
                : "Complete pre-checks to enable scan"}
            </button>
            <FindingsSummary scannerId={scannerId} refreshTrigger={historyRefresh} />
          </div>
          <div className="space-y-5">
            <RunHistoryPanel scannerId={scannerId} refreshTrigger={historyRefresh} />
            <ScanTerminal
              key={runKey}
              scannerId={scannerId}
              scannerLabel={scannerDef.label}
              imageTag={isImageScanner ? (builtImageTag ?? undefined) : undefined}
              autoStart={runKey > 0}
              onDone={handleScanDone}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
