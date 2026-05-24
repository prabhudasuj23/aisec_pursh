"use client";
import { useEffect, useRef, useState } from "react";

interface Props {
  onImageReady: (imageTag: string) => void;
}

const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
const DEFAULT_TAG = "aisec-scan-target:latest";

export default function DockerfilePicker({ onImageReady }: Props) {
  const [dockerfiles, setDockerfiles] = useState<string[]>([]);
  const [selected, setSelected] = useState("pursh/backend/Dockerfile");
  const [building, setBuilding] = useState(false);
  const [buildLines, setBuildLines] = useState<string[]>([]);
  const [builtTag, setBuiltTag] = useState<string | null>(null);
  const [buildError, setBuildError] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    fetch("/api/dockerfiles")
      .then(r => r.json())
      .then(d => {
        const list: string[] = d.dockerfiles ?? [];
        setDockerfiles(list);
        const preferred = list.find(f => f === "pursh/backend/Dockerfile") ?? list[0] ?? "";
        setSelected(preferred);
      })
      .catch(() => setDockerfiles(["pursh/backend/Dockerfile"]));
  }, []);

  async function handleBuild() {
    if (!selected) return;
    setBuildLines([]);
    setBuiltTag(null);
    setBuildError(false);
    setBuilding(true);

    try {
      await fetch("/api/build-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dockerfile_path: selected, tag: DEFAULT_TAG }),
      });
    } catch {
      setBuildLines(["[error] Cannot reach runner. Is it running on port 8002?"]);
      setBuilding(false);
      setBuildError(true);
      return;
    }

    esRef.current?.close();
    const es = new EventSource(`${RUNNER}/stream/build-image`);
    esRef.current = es;

    es.onmessage = (e) => {
      setBuildLines(prev => [...prev, e.data]);
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    es.addEventListener("done", (e) => {
      try {
        const payload = JSON.parse((e as MessageEvent).data);
        if (payload.exit_code === 0 && payload.tag) {
          setBuiltTag(payload.tag);
          onImageReady(payload.tag);
          setBuildError(false);
        } else {
          setBuildError(true);
        }
      } catch { setBuildError(true); }
      setBuilding(false);
      es.close();
      esRef.current = null;
    });

    es.onerror = () => {
      setBuildLines(prev => [...prev, "[error] Lost connection during build."]);
      setBuilding(false);
      setBuildError(true);
      es.close();
      esRef.current = null;
    };
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
      <h2 className="text-white font-black text-sm">Docker Image</h2>
      <p className="text-gray-500 text-xs">Build the target image before scanning. The image scan checks the built container for CVEs.</p>

      <div className="space-y-2">
        <label className="text-xs text-gray-400 font-semibold">Dockerfile</label>
        <select
          value={selected}
          onChange={e => { setSelected(e.target.value); setBuiltTag(null); }}
          disabled={building}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-teal-500 disabled:opacity-50"
        >
          {dockerfiles.map(f => <option key={f} value={f}>{f}</option>)}
        </select>
        <p className="text-gray-600 text-xs font-mono">→ tag: {DEFAULT_TAG}</p>
      </div>

      <button
        onClick={handleBuild}
        disabled={building || !selected}
        className="w-full bg-indigo-700 hover:bg-indigo-600 disabled:opacity-50 text-white text-xs font-bold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        {building ? <><span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />Building…</> : "🐳 Build Image"}
      </button>

      {buildLines.length > 0 && (
        <div className="bg-gray-950 border border-gray-700 rounded-xl h-36 overflow-y-auto p-3 font-mono text-xs">
          {buildLines.map((l, i) => (
            <div key={i} className={l.startsWith("[AISec Runner]") ? "text-teal-400" : l.includes("[error]") ? "text-red-400" : "text-green-300"}>
              {l || " "}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}

      {builtTag && (
        <div className="flex items-center gap-2 bg-green-900/20 border border-green-700/40 rounded-xl px-4 py-2.5">
          <span className="text-green-400">✅</span>
          <span className="text-green-300 text-sm font-semibold">Image ready: <span className="font-mono">{builtTag}</span></span>
        </div>
      )}
      {buildError && !builtTag && (
        <div className="flex items-center justify-between bg-red-900/20 border border-red-700/40 rounded-xl px-4 py-2.5">
          <span className="text-red-300 text-sm">Build failed. Check output above.</span>
          <button onClick={handleBuild} className="text-xs text-red-400 hover:text-red-300 font-semibold">Try again</button>
        </div>
      )}
    </div>
  );
}
