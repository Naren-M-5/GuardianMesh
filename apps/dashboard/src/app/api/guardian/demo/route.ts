import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const host = request.headers.get("host") ?? "";
  const origin = request.headers.get("origin");
  if (!/^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host)
      || (origin && origin !== `http://${host}` && origin !== `https://${host}`)) {
    return NextResponse.json({ error: "Open the demo on localhost." }, { status: 403 });
  }
  let body;
  try { body = await request.json(); }
  catch { return NextResponse.json({ error: "Invalid request" }, { status: 400 }); }
  if (!body || !["intrusion", "late_resident", "delivery", "routine"].includes(body.scenario)) {
    return NextResponse.json({ error: "Unknown scenario" }, { status: 400 });
  }
  const base = (process.env.GUARDIANMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  try {
    const response = await fetch(`${base}/api/v1/demo/${body.scenario}`, {
      method: "POST", signal: AbortSignal.timeout(10000), cache: "no-store",
    });
    if (!response.ok) return NextResponse.json({ error: "Demo could not run." }, { status: response.status });
    const result = await response.json();
    return NextResponse.json({ scenario: result.scenario, score: result.risk.score, level: result.risk.level });
  } catch {
    return NextResponse.json({ error: "Local API unavailable. Start FastAPI and retry." }, { status: 503 });
  }
}
