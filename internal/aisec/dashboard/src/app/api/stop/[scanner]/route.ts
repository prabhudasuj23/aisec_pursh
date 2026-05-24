import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function POST(_req: Request, { params }: { params: Promise<{ scanner: string }> }) {
  const { scanner } = await params;
  try {
    const res = await fetch(`${RUNNER}/stop/${scanner}`, { method: "POST", signal: AbortSignal.timeout(8000) });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ error: "runner_offline" }, { status: 503 });
  }
}
