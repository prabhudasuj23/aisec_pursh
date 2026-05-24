import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function GET(_req: Request, { params }: { params: Promise<{ scanner: string }> }) {
  const { scanner } = await params;
  try {
    const res = await fetch(`${RUNNER}/precheck/${scanner}`, { cache: "no-store", signal: AbortSignal.timeout(20000) });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ scanner_id: scanner, checks: [{ name: "Runner", status: "fail", message: "Cannot reach runner on :8002", blocking: true }], all_pass: false });
  }
}
