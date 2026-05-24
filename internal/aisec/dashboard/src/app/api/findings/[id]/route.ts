import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const res = await fetch(`${RUNNER}/findings/${id}`, { cache: "no-store", signal: AbortSignal.timeout(10000) });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ finding: null });
  }
}
