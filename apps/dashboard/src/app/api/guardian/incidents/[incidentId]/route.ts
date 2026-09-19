import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
const API_BASE = (process.env.GUARDIANMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

type ActionBody = { action?: unknown; resolution?: unknown };

export async function POST(
  request: Request,
  context: { params: Promise<{ incidentId: string }> },
) {
  const { incidentId } = await context.params;
  const body = await request.json() as ActionBody;
  if (body.action !== "acknowledge" && body.action !== "resolve") {
    return NextResponse.json({ error: "Unsupported incident action" }, { status: 400 });
  }
  if (body.action === "resolve" && (typeof body.resolution !== "string" || body.resolution.trim().length < 3)) {
    return NextResponse.json({ error: "Enter a resolution note of at least 3 characters" }, { status: 400 });
  }

  try {
    const response = await fetch(
      `${API_BASE}/api/v1/incidents/${encodeURIComponent(incidentId)}/${body.action}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body.action === "resolve" ? JSON.stringify({ resolution: body.resolution }) : undefined,
        cache: "no-store",
        signal: AbortSignal.timeout(10000),
      },
    );
    const result = await response.json();
    if (!response.ok) {
      return NextResponse.json({ error: result.detail ?? "Incident action failed" }, { status: response.status });
    }
    return NextResponse.json({
      status: result.status,
      title: result.title,
      resolution: result.resolution ?? null,
      updatedAt: result.updated_at,
    });
  } catch {
    return NextResponse.json(
      { error: "GuardianMesh API is unavailable. Keep Terminal 1 running." },
      { status: 503 },
    );
  }
}
