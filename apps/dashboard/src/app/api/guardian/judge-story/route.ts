import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const host = request.headers.get("host") ?? "";
  const origin = request.headers.get("origin");
  if (!/^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host)
      || (origin && origin !== `http://${host}` && origin !== `https://${host}`)) {
    return NextResponse.json({ error: "Judge Mode is available only on localhost." }, { status: 403 });
  }
  const base = (process.env.GUARDIANMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  try {
    const response = await fetch(`${base}/api/v1/demo/judge-story`, {
      method: "POST", cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return NextResponse.json({ error: "Judge story could not run." }, { status: response.status });
    const result = await response.json();
    return NextResponse.json(result);
  } catch {
    return NextResponse.json({ error: "Local API unavailable. Start FastAPI and retry." }, { status: 503 });
  }
}
