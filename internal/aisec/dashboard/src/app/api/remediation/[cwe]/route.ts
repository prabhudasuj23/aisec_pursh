import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function GET(_req: Request, { params }: { params: Promise<{ cwe: string }> }) {
  const { cwe } = await params;
  try {
    const res = await fetch(`${RUNNER}/remediation/${encodeURIComponent(cwe)}`, { cache: "no-store", signal: AbortSignal.timeout(10000) });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ cwe, content: null });
  }
}
