import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
const API_BASE = (process.env.GUARDIANMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function POST() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/integrations/ring/sync`, {
      method: "POST", cache: "no-store", signal: AbortSignal.timeout(30000),
    });
    const body = await response.json();
    if (!response.ok) {
      return NextResponse.json({ error: body.detail ?? "Ring synchronization failed" }, { status: response.status });
    }
    return NextResponse.json(body);
  } catch {
    return NextResponse.json(
      { error: "GuardianMesh API is unavailable. Keep Terminal 1 running." }, { status: 503 },
    );
  }
}
