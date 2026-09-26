import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
const API_BASE = (process.env.GUARDIANMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function GET(
  _request: Request,
  context: { params: Promise<{ incidentId: string }> },
) {
  const { incidentId } = await context.params;
  try {
    const response = await fetch(
      `${API_BASE}/api/v1/incidents/${encodeURIComponent(incidentId)}/explanation`,
      { cache: "no-store", signal: AbortSignal.timeout(10000) },
    );
    const result = await response.json();
    if (!response.ok) {
      return NextResponse.json({ error: result.detail ?? "Explanation unavailable" }, { status: response.status });
    }
    return NextResponse.json(result);
  } catch {
    return NextResponse.json(
      { error: "GuardianMesh API is unavailable. Keep Terminal 1 running." },
      { status: 503 },
    );
  }
}
