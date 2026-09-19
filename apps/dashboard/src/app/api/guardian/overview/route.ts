import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
const API_BASE = (process.env.GUARDIANMESH_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
type JsonRecord = Record<string, unknown>;

async function apiGet(path: string): Promise<JsonRecord> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store", signal: AbortSignal.timeout(5000) });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return (await response.json()) as JsonRecord;
}
const object = (value: unknown): JsonRecord => value && typeof value === "object" ? value as JsonRecord : {};
const list = (value: unknown): JsonRecord[] => Array.isArray(value) ? value.map(object) : [];
const text = (value: unknown, fallback = "Unknown"): string => typeof value === "string" && value.trim() ? value : fallback;
const number = (value: unknown): number => typeof value === "number" && Number.isFinite(value) ? value : 0;

export async function GET() {
  const [healthResult, incidentsResult, eventsResult, devicesResult, syncResult] = await Promise.allSettled([
    apiGet("/api/v1/health"), apiGet("/api/v1/incidents?limit=25"), apiGet("/api/v1/events?limit=25"),
    apiGet("/api/v1/integrations/ring/devices"), apiGet("/api/v1/integrations/ring/sync/status"),
  ]);
  if (healthResult.status === "rejected") {
    return NextResponse.json({ error: "GuardianMesh API is offline", detail: "Start FastAPI on port 8000 and refresh." }, { status: 503 });
  }
  if (incidentsResult.status === "rejected" || eventsResult.status === "rejected") {
    return NextResponse.json({ error: "Assessment data is unavailable", detail: "Incident or event data could not be loaded. Check FastAPI and try again." }, { status: 503 });
  }

  const rawIncidents = incidentsResult.status === "fulfilled" ? list(incidentsResult.value.items) : [];
  const rawEvents = eventsResult.status === "fulfilled" ? list(eventsResult.value.items) : [];
  const rawDevices = devicesResult.status === "fulfilled" ? list(devicesResult.value.data) : [];
  const incidents = rawIncidents.map((item) => {
    const risk = object(item.risk);
    const evidence = list(risk.evidence).map((factor) => ({
      code: text(factor.code, "SIGNAL"), weight: number(factor.weight), value: number(factor.value),
      explanation: text(factor.explanation, "Observed by GuardianMesh."),
    }));
    return {
      incidentId: text(item.incident_id, ""),
      title: text(item.title, "Observed activity"), severity: text(item.severity, "normal"),
      status: text(item.status, "observed"), startedAt: text(item.started_at, new Date().toISOString()),
      resolution: typeof item.resolution === "string" ? item.resolution : null,
      risk: { score: number(risk.score), level: text(risk.level, "normal"), evidence },
    };
  });
  const events = rawEvents.slice(0, 8).map((item) => ({
    type: text(item.type ?? item.event_type, "activity").replaceAll("_", " "), source: text(item.source, "Ring"),
    occurredAt: text(item.occurred_at ?? item.created_at, new Date().toISOString()),
  }));
  // Deliberately discard raw Ring IDs and relationships before responding to the browser.
  const deviceNames = rawDevices.map((item) => text(object(item.attributes).name, "Ring device")).slice(0, 3);
  const sync = syncResult.status === "fulfilled" ? syncResult.value : {};
  const unresolved = incidents.filter((incident) => incident.status !== "resolved");
  const active = incidents.filter((incident) => ["active", "acknowledged"].includes(incident.status));
  const highest = unresolved.reduce<(typeof incidents)[number] | undefined>(
    (current, incident) => !current || incident.risk.score > current.risk.score ? incident : current, undefined,
  );

  return NextResponse.json({
    generatedAt: new Date().toISOString(), api: { online: true, version: text(healthResult.value.version, "0.1.0") },
    ring: {
      online: devicesResult.status === "fulfilled", count: rawDevices.length, names: deviceNames,
      message: devicesResult.status === "fulfilled" ? "Device API reachable" : "Ring unavailable — check your token and connection",
      sync: {
        status: text(sync.status, "never_synced"),
        lastSyncedAt: typeof sync.last_synced_at === "string" ? sync.last_synced_at : null,
        imported: number(sync.imported), duplicates: number(sync.duplicates),
      },
    },
    risk: highest?.risk ?? { score: 0, level: "normal", evidence: [] }, primaryIncident: highest ?? null,
    incidents, events,
    stats: { active: active.length, observed: incidents.length, signals: rawEvents.length },
  });
}
