import { NextResponse } from "next/server";
import { readdirSync, statSync } from "fs";
import { join, relative } from "path";

// Dashboard runs from internal/aisec/dashboard/ — repo root is three levels up
const REPO_ROOT = join(process.cwd(), "..", "..", "..");
const SKIP = new Set(["node_modules", ".git", ".next", "dist", "__pycache__", ".venv"]);

function walk(dir: string, results: string[] = []): string[] {
  try {
    for (const entry of readdirSync(dir)) {
      if (SKIP.has(entry)) continue;
      const full = join(dir, entry);
      try {
        const stat = statSync(full);
        if (stat.isDirectory()) {
          walk(full, results);
        } else if (entry === "Dockerfile" || entry.startsWith("Dockerfile.")) {
          results.push(relative(REPO_ROOT, full).replace(/\\/g, "/"));
        }
      } catch { /* skip inaccessible */ }
    }
  } catch { /* skip inaccessible dir */ }
  return results;
}

export async function GET() {
  const dockerfiles = walk(REPO_ROOT).sort();
  return NextResponse.json({ dockerfiles });
}
