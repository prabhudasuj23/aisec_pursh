"use client";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirectTo") ?? "/";

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [mode, setMode]         = useState<"signin" | "signup">("signin");

  const supabase = createClient();

  // If already signed in, skip the login page
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) router.replace(redirectTo);
    });
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { error } =
        mode === "signin"
          ? await supabase.auth.signInWithPassword({ email, password })
          : await supabase.auth.signUp({ email, password });

      if (error) {
        setError(error.message);
      } else if (mode === "signup") {
        setError("Account created — check your email to confirm, then sign in.");
        setMode("signin");
      } else {
        router.push(redirectTo);
        router.refresh();
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <p className="text-3xl font-black text-white tracking-tight">
            AISec <span className="text-teal-400">↗</span>
          </p>
          <p className="text-gray-400 text-sm mt-2">
            {mode === "signin" ? "Sign in to access scan history and AI intelligence" : "Create your AISec account"}
          </p>
        </div>

        {/* Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl">
          <h2 className="text-lg font-bold text-white mb-6">
            {mode === "signin" ? "Sign In" : "Create Account"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5">Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
              />
            </div>

            {error && (
              <p className={`text-xs rounded-lg px-3 py-2 ${
                error.startsWith("Account created")
                  ? "bg-teal-900/30 text-teal-400 border border-teal-800"
                  : "bg-red-900/30 text-red-400 border border-red-800"
              }`}>
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-600 hover:bg-teal-500 disabled:bg-teal-900 disabled:text-teal-700 text-white font-semibold rounded-lg py-2.5 text-sm transition-colors"
            >
              {loading ? "Please wait…" : mode === "signin" ? "Sign In" : "Create Account"}
            </button>
          </form>

          <div className="mt-4 pt-4 border-t border-gray-800 text-center">
            {mode === "signin" ? (
              <p className="text-xs text-gray-500">
                No account?{" "}
                <button onClick={() => { setMode("signup"); setError(null); }} className="text-teal-400 hover:text-teal-300 font-semibold">
                  Create one
                </button>
              </p>
            ) : (
              <p className="text-xs text-gray-500">
                Already have an account?{" "}
                <button onClick={() => { setMode("signin"); setError(null); }} className="text-teal-400 hover:text-teal-300 font-semibold">
                  Sign in
                </button>
              </p>
            )}
          </div>
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-gray-700 mt-6">
          AISec · Enterprise DevSecOps Platform · Pursh scan target
        </p>
      </div>
    </div>
  );
}
