import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const qs = searchParams.toString();
  try {
    const res = await fetch(`${RUNNER}/findings${qs ? `?${qs}` : ""}`, { cache: "no-store", signal: AbortSignal.timeout(15000) });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ findings: [], error: "runner_offline" });
  }
}
