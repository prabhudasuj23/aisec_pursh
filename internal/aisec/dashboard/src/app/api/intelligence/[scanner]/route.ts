/**
 * GET /api/intelligence/[scanner]
 *
 * Two-phase flow:
 *  1. Check Supabase ai_analyses for a recent cached result — if found
 *     and the result file mtime is unchanged, return it without calling
 *     the runner (saves DeepSeek API cost and latency).
 *  2. Otherwise, forward to the runner which calls DeepSeek and saves
 *     the new analysis to Supabase.
 *
 * Requires an authenticated session.
 */
import { NextResponse, type NextRequest } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-server";

const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ scanner: string }> }
) {
  const { scanner } = await params;
  const supabase = await createServerSupabaseClient();

  // Auth gate
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Check for a recent AI analysis in Supabase (last 2 hours)
  const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
  const { data: cached } = await supabase
    .from("ai_analyses")
    .select("response_parsed, latency_ms, created_at, cached")
    .eq("scanner_id", scanner)
    .eq("cached", false)
    .is("error", null)
    .gte("created_at", twoHoursAgo)
    .order("created_at", { ascending: false })
    .limit(1)
    .single();

  if (cached?.response_parsed) {
    return NextResponse.json({
      scanner,
      status: "ok",
      cached: true,
      cached_at: cached.created_at,
      latency_ms: cached.latency_ms,
      ...cached.response_parsed,
    });
  }

  // No recent cache — call runner which will invoke DeepSeek and save to Supabase
  try {
    const res = await fetch(`${RUNNER}/intelligence/${scanner}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(60000), // DeepSeek can take up to 30s
    });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ status: "runner_offline" });
  }
}
