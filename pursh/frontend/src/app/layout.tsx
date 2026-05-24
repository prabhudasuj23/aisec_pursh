import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "Pursh — Healthcare Made Simple",
  description:
    "Connect with board-certified clinicians online. Get personalised care plans delivered quickly, privately, and affordably.",
  robots: "noindex, nofollow",
};

// REQUIRED per CLAUDE.md §1.2 — must appear on every public page
const LEGAL_DISCLAIMER =
  "Pursh is not a real medical service. Content on this site is for demonstration purposes only and does not constitute medical advice. Always consult a qualified healthcare professional.";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.className}>
      <body className="bg-pursh-silver text-pursh-charcoal antialiased">
        <Navbar />
        <div className="min-h-screen">
          {children}
        </div>

        {/* ── FOOTER ──────────────────────────────────────────────── */}
        <footer className="bg-pursh-ink text-white pt-16 pb-8 px-6">
          <div className="max-w-7xl mx-auto">

            {/* Top grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-10 pb-12 border-b border-white/10">

              {/* Brand */}
              <div className="col-span-2 md:col-span-1">
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-8 h-8 rounded-2xl bg-pursh-teal flex items-center justify-center text-white font-bold text-sm">P</span>
                  <span className="font-bold text-lg">Pursh</span>
                </div>
                <p className="text-white/55 text-xs leading-relaxed max-w-xs">
                  Quality healthcare, on your schedule. Board-certified
                  clinicians available online — no waiting rooms.
                </p>
              </div>

              {/* Conditions */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-pursh-aqua mb-4">Conditions</p>
                <ul className="space-y-2.5 text-sm text-white/65">
                  {[
                    ["Primary Care",      "/symptoms"],
                    ["Skin & Hair",       "/symptoms?category=skin-hair"],
                    ["Mental Health",     "/symptoms?category=mental-health"],
                    ["Weight Care",       "/symptoms?category=weight-care"],
                    ["General Wellness",  "/symptoms?category=wellness"],
                  ].map(([label, href]) => (
                    <li key={label}><a href={href} className="hover:text-white transition-colors">{label}</a></li>
                  ))}
                </ul>
              </div>

              {/* Platform */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-pursh-aqua mb-4">Platform</p>
                <ul className="space-y-2.5 text-sm text-white/65">
                  {[
                    ["Symptom Checker", "/symptoms"],
                    ["Our Doctors",     "/doctors"],
                    ["Sign Up",         "/signup"],
                    ["Sign In",         "/login"],
                  ].map(([label, href]) => (
                    <li key={label}><a href={href} className="hover:text-white transition-colors">{label}</a></li>
                  ))}
                </ul>
              </div>

              {/* Legal */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-pursh-aqua mb-4">Legal</p>
                <ul className="space-y-2.5 text-sm text-white/65">
                  <li><span className="cursor-default">Privacy Policy <span className="text-xs text-white/30">(coming soon)</span></span></li>
                  <li><span className="cursor-default">Terms of Service <span className="text-xs text-white/30">(coming soon)</span></span></li>
                  <li><span className="cursor-default">Cookie Policy <span className="text-xs text-white/30">(coming soon)</span></span></li>
                </ul>
              </div>

            </div>

            {/* Bottom — legal disclaimer + copyright */}
            <div className="pt-8 space-y-3 text-xs text-white/40">
              <p className="leading-relaxed max-w-4xl">{LEGAL_DISCLAIMER}</p>
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                <p>© {new Date().getFullYear()} Pursh. All rights reserved.</p>
                <p>Not medical advice · Not a licensed healthcare provider</p>
              </div>
            </div>

            {/* Brand watermark */}
            <p className="text-center mt-10 text-[80px] md:text-[120px] font-bold text-white/[0.04] leading-none select-none">
              Pursh
            </p>

          </div>
        </footer>
      </body>
    </html>
  );
}
