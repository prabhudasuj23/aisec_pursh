"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase";
import type { User } from "@supabase/supabase-js";

const NAV = [
  { href: "/",           label: "Scanners" },
  { href: "/findings",   label: "Findings" },
  { href: "/compliance", label: "Compliance" },
];

export default function Navbar() {
  const path = usePathname();
  const router = useRouter();
  const supabase = createClient();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  async function signOut() {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <nav className="sticky top-0 z-40 border-b border-gray-800 bg-gray-950/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">

        {/* Left: brand + nav links */}
        <div className="flex items-center gap-6">
          <Link href="/" className="font-black text-white text-lg tracking-tight">
            AISec <span className="text-teal-400">↗</span>
          </Link>
          <div className="flex items-center gap-1">
            {NAV.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
                  path === href
                    ? "bg-gray-800 text-white"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                {label}
              </Link>
            ))}
          </div>
        </div>

        {/* Right: runner status + auth */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-600 font-mono hidden sm:block">
            Pursh · target app
          </span>
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" title="Runner online" />

          {user ? (
            <div className="flex items-center gap-2 ml-2 pl-3 border-l border-gray-800">
              <span className="text-xs text-gray-400 hidden sm:block max-w-[140px] truncate">
                {user.email}
              </span>
              <button
                onClick={signOut}
                className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
              >
                Sign out
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="ml-2 text-xs font-semibold px-2.5 py-1 rounded-lg bg-teal-700 text-white hover:bg-teal-600 transition-colors"
            >
              Sign in
            </Link>
          )}
        </div>

      </div>
    </nav>
  );
}
