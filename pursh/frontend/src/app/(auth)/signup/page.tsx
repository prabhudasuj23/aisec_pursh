"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();
  const supabase = createClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    const { error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { role: "patient" },
      },
    });
    setLoading(false);

    if (authError) {
      setError("Could not create account. Please try again.");
      return;
    }

    setSuccess(true);
  }

  if (success) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4 py-16 bg-pursh-cream">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-10 w-full max-w-md text-center">
          <div className="w-16 h-16 rounded-full bg-pursh-mint flex items-center justify-center text-3xl mx-auto mb-5">
            ✉️
          </div>
          <h1 className="text-2xl font-bold text-pursh-charcoal mb-2">Check your email</h1>
          <p className="text-pursh-muted text-sm leading-relaxed">
            We sent a confirmation link to{" "}
            <strong className="text-pursh-charcoal">{email}</strong>.
            Click it to activate your account.
          </p>
          <Link
            href="/login"
            className="inline-block mt-6 text-sm font-medium text-pursh-green hover:underline"
          >
            Back to sign in
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-16 bg-pursh-cream">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <span className="w-9 h-9 rounded-xl bg-pursh-green flex items-center justify-center text-white font-bold">
            P
          </span>
          <span className="font-bold text-2xl text-pursh-charcoal">Pursh</span>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h1 className="text-2xl font-bold text-pursh-charcoal mb-1">Create your account</h1>
          <p className="text-pursh-muted text-sm mb-7">
            Start your healthcare journey with Pursh
          </p>

          <div className="bg-pursh-mint border border-pursh-teal/20 rounded-2xl p-3 mb-6 text-xs text-pursh-graphite">
            ⚠️ Demonstration project — use a test email only. Do not enter real personal information.
          </div>

          {error && (
            <div className="bg-pursh-silver border border-pursh-graphite/15 text-pursh-graphite rounded-2xl p-3 mb-6 text-sm flex items-start gap-2">
              <span className="mt-0.5">⚠</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSignup} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-pursh-charcoal mb-1.5">
                Email address
              </label>
              <input
                id="email" type="email" autoComplete="email" required
                value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-pursh-green focus:border-transparent transition-all placeholder:text-gray-400"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-pursh-charcoal mb-1.5">
                Password
              </label>
              <input
                id="password" type="password" autoComplete="new-password" required
                value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-pursh-green focus:border-transparent transition-all placeholder:text-gray-400"
                placeholder="At least 8 characters"
              />
            </div>
            <div>
              <label htmlFor="confirm" className="block text-sm font-medium text-pursh-charcoal mb-1.5">
                Confirm password
              </label>
              <input
                id="confirm" type="password" autoComplete="new-password" required
                value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-pursh-green focus:border-transparent transition-all placeholder:text-gray-400"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit" disabled={loading}
              className="w-full bg-pursh-green text-white py-3 rounded-xl font-semibold hover:bg-pursh-green-light transition-colors disabled:opacity-50 mt-2"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-pursh-muted mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-pursh-green font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          By creating an account you agree this is a synthetic demo. Do not enter real health data.
        </p>
      </div>
    </main>
  );
}
