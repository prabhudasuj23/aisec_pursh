import { NextResponse } from "next/server";
const RUNNER = process.env.NEXT_PUBLIC_RUNNER_URL ?? "http://localhost:8002";
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const qs = searchParams.toString();
  try {
    const res = await fetch(`${RUNNER}/export${qs ? `?${qs}` : ""}`, { cache: "no-store", signal: AbortSignal.timeout(30000) });
    const contentType = res.headers.get("content-type") ?? "application/octet-stream";
    const disposition = res.headers.get("content-disposition") ?? "";
    const body = await res.arrayBuffer();
    return new NextResponse(body, { headers: { "Content-Type": contentType, "Content-Disposition": disposition } });
  } catch {
    return NextResponse.json({ error: "runner_offline" }, { status: 503 });
  }
}
