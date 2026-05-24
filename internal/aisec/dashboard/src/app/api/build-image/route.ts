import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function POST(req: Request) {
  const body = await req.json();
  try {
    const res = await fetch(`${RUNNER}/build-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10000),
    });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ error: "runner_offline" }, { status: 503 });
  }
}
