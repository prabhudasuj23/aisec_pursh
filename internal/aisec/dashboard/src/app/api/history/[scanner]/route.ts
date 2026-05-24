/**
 * GET /api/history/[scanner]
 *
 * Returns the last 10 scan runs for a scanner, fetched directly from
 * the Supabase scan_runs table.  Requires an authenticated session —
 * RLS enforces this at the database level; we also check here for a
 * clear 401 response rather than an empty data array.
 */
import { NextResponse, type NextRequest } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-server";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ scanner: string }> }
) {
  const { scanner } = await params;
  const supabase = await createServerSupabaseClient();

  // Verify session — unauthenticated callers get 401
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data, error } = await supabase
    .from("scan_runs")
    .select(
      "run_id, scanner_id, scanner_name, started_at, finished_at, " +
      "exit_code, status, counts, findings_count, risk_score, delta, effort_minutes"
    )
    .eq("scanner_id", scanner)
    .order("created_at", { ascending: false })
    .limit(10);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({
    scanner_id: scanner,
    source: "supabase",
    history: data ?? [],
  });
}
