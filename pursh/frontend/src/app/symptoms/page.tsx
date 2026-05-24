"use client";

import { useState, useRef, useEffect } from "react";
import { Doctor, DoctorsApiResponse } from "@/lib/types/doctor";
import type { AIMessage, QuestionResponse, ResultResponse, SymptomCheckResponse } from "@/app/api/symptom-check/route";

// ─── Avatar helper (same as doctors page) ────────────────────────────────────
const AVATAR_COMBOS = [
  "bg-pursh-teal text-white",
  "bg-pursh-graphite text-white",
  "bg-pursh-aqua text-pursh-charcoal",
  "bg-pursh-mint text-pursh-charcoal",
];
function avatarClass(id: string) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
  return AVATAR_COMBOS[Math.abs(h) % AVATAR_COMBOS.length];
}

// ─── Doctor popup ─────────────────────────────────────────────────────────────
function DoctorModal({
  specialty,
  onClose,
}: {
  specialty: string;
  onClose: () => void;
}) {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookModal, setBookModal] = useState(false);

  useEffect(() => {
    fetch(`/api/doctors?specialty=${encodeURIComponent(specialty)}`)
      .then((r) => r.json() as Promise<DoctorsApiResponse>)
      .then((d) => setDoctors(d.doctors.slice(0, 6)))
      .finally(() => setLoading(false));
  }, [specialty]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 px-0 sm:px-4"
      onClick={onClose}
    >
      <div
        className="bg-white w-full sm:max-w-2xl rounded-t-3xl sm:rounded-3xl shadow-2xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-gray-100">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-pursh-teal mb-0.5">
              Recommended specialists
            </p>
            <h2 className="text-xl font-black text-pursh-charcoal">{specialty}</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-pursh-silver flex items-center justify-center text-pursh-slate hover:text-pursh-charcoal"
          >
            ✕
          </button>
        </div>

        {/* Doctor list */}
        <div className="overflow-y-auto flex-1 px-6 py-4 space-y-3">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse flex items-center gap-4 p-4 rounded-2xl border border-gray-100">
                <div className="w-11 h-11 rounded-full bg-pursh-silver" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-pursh-silver rounded w-1/2" />
                  <div className="h-3 bg-pursh-silver rounded w-3/4" />
                </div>
              </div>
            ))
          ) : doctors.length === 0 ? (
            <p className="text-center text-pursh-muted py-8">No doctors found.</p>
          ) : (
            doctors.map((d) => (
              <div
                key={d.id}
                className="flex items-center gap-4 p-4 rounded-2xl border border-gray-100 hover:border-pursh-teal/30 hover:bg-pursh-mint/20 transition-colors"
              >
                <div
                  className={`w-11 h-11 rounded-full flex items-center justify-center text-xs font-black shrink-0 ${avatarClass(d.id)}`}
                >
                  {d.initials}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-pursh-charcoal text-sm truncate">{d.name}</p>
                  <p className="text-xs text-pursh-slate truncate">
                    {[d.hospital, d.city].filter(Boolean).join(" · ")}
                  </p>
                  {d.nmcRegNo && (
                    <p className="text-xs font-mono text-pursh-muted">{d.nmcRegNo}</p>
                  )}
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => setBookModal(true)}
                    className="text-xs font-bold bg-pursh-teal text-white px-3 py-1.5 rounded-full hover:bg-pursh-teal-deep transition-colors"
                  >
                    Book
                  </button>
                  <a
                    href="https://www.nmc.org.in/information-desk/indian-medical-register/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-bold text-pursh-teal border border-pursh-teal px-3 py-1.5 rounded-full hover:bg-pursh-mint transition-colors"
                  >
                    Verify ↗
                  </a>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="px-6 pb-6 pt-2">
          <a
            href={`/doctors?specialty=${encodeURIComponent(specialty)}`}
            className="block text-center text-sm font-bold text-pursh-teal hover:underline"
          >
            See all doctors →
          </a>
        </div>
      </div>

      {/* Book coming-soon modal */}
      {bookModal && (
        <div
          className="fixed inset-0 z-60 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setBookModal(false)}
        >
          <div
            className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-2xl mb-2">🗓️</p>
            <h3 className="text-xl font-black text-pursh-charcoal mb-2">Coming soon</h3>
            <p className="text-pursh-slate text-sm mb-6">
              Online booking is on the way. Your specialist recommendation is ready — save the doctor&apos;s name and contact them directly.
            </p>
            <button
              onClick={() => setBookModal(false)}
              className="w-full border border-pursh-graphite/20 text-pursh-charcoal py-2.5 rounded-full text-sm font-bold hover:border-pursh-teal hover:text-pursh-teal transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Option pill ──────────────────────────────────────────────────────────────
function OptionPill({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-5 py-3 rounded-2xl border text-sm font-semibold transition-all ${
        selected
          ? "bg-pursh-teal text-white border-pursh-teal shadow-sm"
          : "bg-white text-pursh-charcoal border-pursh-graphite/15 hover:border-pursh-teal hover:text-pursh-teal"
      }`}
    >
      {label}
    </button>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
interface Step {
  question: string;
  options: string[];
  selected: string | null;
}

export default function SymptomsPage() {
  const [input, setInput] = useState("");
  const [started, setStarted] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [showDoctors, setShowDoctors] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  // Scroll the chat container (not the window) to bottom when new content appears
  useEffect(() => {
    const el = chatRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [steps, loading, result]);

  async function callAI(msgs: AIMessage[]) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/symptom-check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: msgs }),
      });
      const data = (await res.json()) as SymptomCheckResponse;

      if (data.type === "question") {
        const q = data as QuestionResponse;
        setSteps((prev) => [...prev, { question: q.question, options: q.options, selected: null }]);
      } else if (data.type === "result") {
        setResult(data as ResultResponse);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } catch {
      setError("Could not reach AI. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim().length < 5) return;
    const initMsgs: AIMessage[] = [{ role: "user", content: input.trim() }];
    setMessages(initMsgs);
    setStarted(true);
    await callAI(initMsgs);
  }

  async function handleOption(stepIndex: number, option: string) {
    // Mark selected instantly
    setSteps((prev) =>
      prev.map((s, i) => (i === stepIndex ? { ...s, selected: option } : s))
    );

    // Build message history
    const newMsg: AIMessage = { role: "user", content: option };
    // Reconstruct full message thread: initial symptom + Q&A pairs
    const thread: AIMessage[] = [...messages];
    // Add assistant questions and user answers up to this point
    steps.forEach((s, i) => {
      thread.push({ role: "assistant", content: JSON.stringify({ type: "question", question: s.question, options: s.options }) });
      if (i < stepIndex) thread.push({ role: "user", content: s.selected ?? "" });
    });
    thread.push(newMsg);

    const updated = [...messages, newMsg];
    setMessages(updated);
    await callAI(thread);
  }

  function reset() {
    setInput("");
    setStarted(false);
    setSteps([]);
    setMessages([]);
    setResult(null);
    setShowDoctors(false);
    setError(null);
    setLoading(false);
  }

  const isEmergency = result?.urgency === "emergency";

  return (
    <>
      {/* Pin to viewport height so footer never intrudes */}
      <main className="flex flex-col" style={{ height: "calc(100vh - 3.5rem)" }}>

        {/* Pinned header — never scrolls */}
        <div className="shrink-0 border-b border-pursh-graphite/10 bg-white">
          <div className="max-w-xl mx-auto px-4 pt-6 pb-4">
            <p className="text-xs font-bold uppercase tracking-widest text-pursh-teal mb-1">Symptom checker</p>
            <h1 className="text-2xl font-black text-pursh-ink leading-tight">What are you experiencing?</h1>
          </div>
        </div>

        {/* Scrollable chat — fills remaining height, window never scrolls */}
        <div ref={chatRef} className="flex-1 overflow-y-auto bg-pursh-silver">
          <div className="max-w-xl mx-auto px-4 py-6 space-y-4">

            {/* Emergency strip */}
            <div className="bg-red-50 border border-red-200 rounded-2xl p-3 text-xs text-red-800 flex items-start gap-2">
              <span className="shrink-0">🚨</span>
              <span>Not for emergencies — call <strong>112</strong> immediately for chest pain, difficulty breathing, or any life-threatening symptom.</span>
            </div>

        {/* Initial input */}
        {!started && (
          <form onSubmit={handleStart} className="bg-white rounded-[1.5rem] p-6 border border-pursh-graphite/10 shadow-sm">
            <label htmlFor="symptoms" className="block text-sm font-bold text-pursh-ink mb-2">
              Describe your symptoms
            </label>
            <textarea
              id="symptoms"
              rows={4}
              maxLength={500}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="E.g. I've had a persistent rash on my arms for a week…"
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-pursh-teal resize-none placeholder:text-gray-400 transition-all"
            />
            <div className="text-right text-xs text-pursh-muted mb-4">{input.length}/500</div>
            <button
              type="submit"
              disabled={input.trim().length < 5}
              className="w-full bg-pursh-teal text-white py-3 rounded-full font-bold hover:bg-pursh-teal-deep transition-colors disabled:opacity-40"
            >
              Start →
            </button>
          </form>
        )}

        {/* Conversation */}
        {started && (
          <div className="space-y-4">
            {/* User's initial symptom bubble */}
            <div className="flex justify-end">
              <div className="bg-pursh-teal text-white text-sm font-medium px-5 py-3 rounded-2xl rounded-br-md max-w-xs">
                {input}
              </div>
            </div>

            {/* Q&A steps */}
            {steps.map((step, i) => (
              <div key={i} className="space-y-3">
                {/* AI question */}
                <div className="flex justify-start">
                  <div className="bg-white border border-pursh-graphite/10 text-pursh-charcoal text-sm font-semibold px-5 py-3 rounded-2xl rounded-bl-md max-w-xs shadow-sm">
                    {step.question}
                  </div>
                </div>
                {/* Options — show only for last unanswered, or show chosen for answered */}
                {step.selected ? (
                  <div className="flex justify-end">
                    <div className="bg-pursh-teal text-white text-sm font-medium px-5 py-3 rounded-2xl rounded-br-md max-w-xs">
                      {step.selected}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {step.options.map((opt, optIdx) => (
                      <OptionPill
                        key={`${i}-${optIdx}`}
                        label={opt}
                        selected={false}
                        onClick={() => handleOption(i, opt)}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Loading */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-pursh-graphite/10 px-5 py-3 rounded-2xl rounded-bl-md shadow-sm flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-pursh-teal animate-bounce [animation-delay:0ms]" />
                  <span className="w-3 h-3 rounded-full bg-pursh-teal animate-bounce [animation-delay:150ms]" />
                  <span className="w-3 h-3 rounded-full bg-pursh-teal animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-5 py-3 rounded-2xl">
                {error}
              </div>
            )}

            {/* Result */}
            {result && (
              <div className={`rounded-[1.5rem] p-6 border shadow-sm ${isEmergency ? "bg-red-50 border-red-200" : "bg-white border-pursh-graphite/10"}`}>
                {isEmergency ? (
                  <>
                    <p className="text-2xl mb-2">🚨</p>
                    <h2 className="text-xl font-black text-red-700 mb-2">Seek emergency care now</h2>
                    <p className="text-red-600 text-sm">Call <strong>112</strong> immediately. Do not wait for a virtual consultation.</p>
                  </>
                ) : (
                  <>
                    <p className="text-2xl mb-2">✅</p>
                    <h2 className="text-xl font-black text-pursh-charcoal mb-1">We recommend</h2>
                    <p className="text-pursh-teal text-lg font-black mb-4">{result.specialty}</p>
                    <p className="text-xs text-pursh-muted mb-5">
                      Not medical advice — always consult a qualified healthcare professional.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3">
                      <button
                        onClick={() => setShowDoctors(true)}
                        className="flex-1 bg-pursh-teal text-white py-3 rounded-full text-sm font-bold hover:bg-pursh-teal-deep transition-colors"
                      >
                        Find a clinician →
                      </button>
                      <button
                        onClick={reset}
                        className="flex-1 border border-pursh-graphite/20 text-pursh-charcoal py-3 rounded-full text-sm font-bold hover:border-pursh-teal hover:text-pursh-teal transition-colors"
                      >
                        Start over
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Start over link */}
            {!result && !loading && (
              <button onClick={reset} className="text-xs text-pursh-muted hover:text-pursh-teal underline">
                Start over
              </button>
            )}
          </div>
        )}

          </div>{/* end inner max-w */}
        </div>{/* end scrollable chat */}
      </main>

      {/* Doctor popup */}
      {showDoctors && result && (
        <DoctorModal specialty={result.specialty} onClose={() => setShowDoctors(false)} />
      )}
    </>
  );
}
