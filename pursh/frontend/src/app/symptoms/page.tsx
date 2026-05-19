"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

const EMERGENCY_NOTE =
  "If you are experiencing a medical emergency, call 911 immediately. Do not use this form.";

const DISCLAIMER =
  "⚠️ NOT MEDICAL ADVICE. Demonstration project. Do not enter real symptoms or personal health information.";

interface SymptomResult {
  suggested_specialty: string;
  urgency: string;
  guidance: string;
  disclaimer: string;
}

export default function SymptomsPage() {
  const [symptoms, setSymptoms] = useState("");
  const [result, setResult] = useState<SymptomResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (symptoms.trim().length < 3) {
      setError("Please describe your symptoms.");
      return;
    }
    if (symptoms.length > 500) {
      setError("Keep your description under 500 characters.");
      return;
    }

    setLoading(true);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_PURSH_API_URL ?? "http://localhost:8001"}/api/v1/symptoms/check`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({ symptoms }),
        }
      );

      if (!res.ok) {
        setError("Unable to process your request. Please try again.");
        return;
      }

      const data: SymptomResult = await res.json();
      setResult(data);
    } catch {
      setError("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-2xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">Symptom checker</h1>
      <p className="text-pursh-muted mb-6 text-sm">{DISCLAIMER}</p>

      <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-8 text-sm text-red-800">
        🚨 {EMERGENCY_NOTE}
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
        <label htmlFor="symptoms" className="block font-semibold mb-2">
          Describe your symptoms (synthetic/test only)
        </label>
        <textarea
          id="symptoms"
          rows={5}
          maxLength={500}
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="E.g. mild headache and fatigue for 2 days (use test data only)"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pursh-green resize-none"
        />
        <div className="text-right text-xs text-pursh-muted mb-4">
          {symptoms.length}/500
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-4 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-pursh-green text-white py-2.5 rounded-lg font-semibold hover:bg-pursh-green-light transition-colors disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Check symptoms"}
        </button>
      </form>

      {result && (
        <div className="mt-8 bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h2 className="text-xl font-bold mb-4">
            {result.urgency === "emergency" ? "🚨 Emergency" : "✅ Results"}
          </h2>
          <div className="space-y-3 text-sm">
            <div>
              <span className="font-semibold">Suggested specialty: </span>
              <span className="text-pursh-green">{result.suggested_specialty}</span>
            </div>
            <div>
              <span className="font-semibold">Urgency: </span>
              <span className={result.urgency === "emergency" ? "text-red-600 font-bold" : "text-gray-700"}>
                {result.urgency}
              </span>
            </div>
            <div>
              <span className="font-semibold">Guidance: </span>
              <span>{result.guidance}</span>
            </div>
          </div>
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3 mt-6">
            {result.disclaimer}
          </p>
        </div>
      )}
    </main>
  );
}
