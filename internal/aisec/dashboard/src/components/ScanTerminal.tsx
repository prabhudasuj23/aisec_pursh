"use client";
import { useEffect, useRef, useState } from "react";

interface Props {
  scannerId: string;
  scannerLabel: string;
  imageTag?: string;
  autoStart?: boolean;
  onDone?: (exitCode: number) => void;
}

const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";

export default function ScanTerminal({ scannerId, scannerLabel, imageTag, autoStart = false, onDone }: Props) {
  const [lines, setLines] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [exitCode, setExitCode] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);
  // Guards against React StrictMode double-invoke and EventSource auto-reconnect
  const startedRef = useRef(false);

  useEffect(() => {
    if (!autoStart) return;
    // Prevent double-start from StrictMode or stale effect re-runs
    if (startedRef.current) return;
    startedRef.current = true;

    esRef.current?.close();
    setLines([]);
    setDone(false);
    setExitCode(null);

    const params = new URLSearchParams();
    if (imageTag) params.set("image", imageTag);
    const url = `${RUNNER}/stream/${scannerId}${params.toString() ? `?${params}` : ""}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      setLines(prev => [...prev, e.data]);
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    es.addEventListener("done", (e) => {
      try {
        const payload = JSON.parse((e as MessageEvent).data);
        setExitCode(payload.exit_code ?? 0);
        onDone?.(payload.exit_code ?? 0);
      } catch { setExitCode(0); onDone?.(0); }
      setDone(true);
      es.close();
      esRef.current = null;
    });

    es.onerror = () => {
      // Close immediately — prevents EventSource auto-reconnect from spawning a second scan
      es.close();
      esRef.current = null;
      setDone(prev => {
        if (!prev) {
          setLines(l => [...l, "[error] Lost connection to runner. Check the runner is running on :8002."]);
          onDone?.(-1);
        }
        return true;
      });
    };

    return () => { es.close(); esRef.current = null; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart, scannerId, imageTag]);

  if (!autoStart && lines.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex items-center justify-center h-32">
        <p className="text-gray-600 text-sm">Terminal output will appear here when you run the scan.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-800 bg-gray-950/50">
        <div className="flex items-center gap-2">
          {!done ? <span className="w-2.5 h-2.5 rounded-full bg-teal-400 animate-pulse" />
                 : exitCode === 0 ? <span className="text-green-400 text-sm">✅</span>
                 : <span className="text-yellow-400 text-sm">⚠</span>}
          <span className="text-white text-xs font-bold">{scannerLabel}</span>
          {!done && <span className="text-gray-500 text-xs">Running…</span>}
          {done && exitCode !== null && <span className="text-gray-500 text-xs">Exit {exitCode}</span>}
        </div>
        {imageTag && <span className="text-xs text-teal-400 font-mono">{imageTag}</span>}
      </div>
      <div className="h-64 overflow-y-auto p-4 font-mono text-xs leading-relaxed">
        {lines.length === 0 && !done && <span className="text-gray-600">Connecting to runner…</span>}
        {lines.map((l, i) => (
          <div key={i} className={
            l.startsWith("[AISec Runner]") ? "text-teal-400" :
            l.includes("[error]")          ? "text-red-400"  :
            l.includes("ERROR") || l.includes("CRITICAL") ? "text-red-400" :
            l.includes("WARN")  || l.includes("HIGH")     ? "text-yellow-400" :
            "text-green-300"
          }>{l || " "}</div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
