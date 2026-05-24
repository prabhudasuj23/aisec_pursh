import { NextResponse } from "next/server";

const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";

export async function GET() {
  try {
    const res = await fetch(`${RUNNER}/scanners-status`, {
      // 30s server-side cache matches the runner's own cache window
      next: { revalidate: 30 },
      signal: AbortSignal.timeout(8000),
    });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ scanners: {} });
  }
}
