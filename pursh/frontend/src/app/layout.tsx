import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pursh — Healthcare Made Simple",
  description:
    "Demonstration project — not a real medical service. Synthetic test data only. This is a security-engineering portfolio project.",
  robots: "noindex, nofollow", // demo app should not be indexed
};

const DISCLAIMER =
  "⚠️ Demonstration project — not a real medical service. Do not enter real symptoms, conditions, or PHI. Synthetic test data only.";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-pursh-cream text-pursh-charcoal font-sans antialiased">
        {/* REQUIRED disclaimer banner — must appear on every page (CLAUDE.md §1.2) */}
        <div className="w-full bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-sm text-amber-800">
          {DISCLAIMER}
        </div>
        {children}
        {/* Footer disclaimer */}
        <footer className="border-t border-gray-200 mt-16 py-8 px-4 text-center text-xs text-gray-500">
          <p>{DISCLAIMER}</p>
          <p className="mt-1">
            AISec security platform demo · Built by{" "}
            <a href="https://aivistix.com" className="underline">
              Aivistix
            </a>
          </p>
        </footer>
      </body>
    </html>
  );
}
