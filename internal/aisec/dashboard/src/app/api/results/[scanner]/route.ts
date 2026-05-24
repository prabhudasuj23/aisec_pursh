import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function GET(_req: Request, { params }: { params: Promise<{ scanner: string }> }) {
  const { scanner } = await params;
  try {
    const res = await fetch(`${RUNNER}/results/${scanner}`, { cache: "no-store", signal: AbortSignal.timeout(10000) });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ status: "runner_offline" });
  }
}
