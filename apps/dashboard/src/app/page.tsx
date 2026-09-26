"use client";

import { useCallback, useEffect, useState } from "react";

type Factor = { code: string; weight: number; value: number; explanation: string };
type Incident = { incidentId: string; title: string; severity: string; status: string; startedAt: string; resolution: string | null; risk: { score: number; level: string; evidence: Factor[]; context?: { assessment_mode?: string; baseline_sample_count?: number; familiarity_adjustment?: number } } };
type Overview = {
  generatedAt: string; api: { online: boolean; version: string };
  ring: { online: boolean; count: number; names: string[]; message: string; sync: { status: string; lastSyncedAt: string | null; imported: number; duplicates: number } };
  risk: { score: number; level: string; evidence: Factor[] }; primaryIncident: Incident | null;
  baseline: { status: string; sampleCount: number; minimumSamples: number; confidence: number; activeHours: number[]; medianDurationSeconds: number; privacy: string };
  incidents: Incident[]; events: { type: string; source: string; occurredAt: string }[];
  stats: { active: number; observed: number; signals: number };
};

const Shield = ({ size = 24 }: { size?: number }) => <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 2.7 20 6v5.2c0 5.2-3.4 9.2-8 10.2-4.6-1-8-5-8-10.2V6l8-3.3Z" stroke="currentColor" strokeWidth="1.7"/><path d="m8.7 12 2.1 2.1 4.7-4.8" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>;
const formatTime = (value: string) => { const date = new Date(value); return Number.isNaN(date.getTime()) ? "Recently" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); };
const label = (value: string) => value.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());

export default function Dashboard() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");
  const [incidentAction, setIncidentAction] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [showResolution, setShowResolution] = useState(false);
  const [resolutionNote, setResolutionNote] = useState("");
  const [resolutionOutcome, setResolutionOutcome] = useState("harmless_activity");
  const [demoBusy, setDemoBusy] = useState(false);
  const [demoMessage, setDemoMessage] = useState("");
  async function runDemo(scenario: string) {
    setDemoBusy(true); setDemoMessage("");
    try {
      const response = await fetch("/api/guardian/demo", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }), signal: AbortSignal.timeout(15000),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error ?? "Demo failed");
      setDemoMessage(`Simulation: ${result.scenario} — score ${result.score}, ${result.level}. Saved to local history.`);
      await refresh();
    } catch (cause) { setDemoMessage(cause instanceof Error ? cause.message : "Demo failed"); }
    finally { setDemoBusy(false); }
  }
  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/guardian/overview", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? body.error ?? "Dashboard unavailable");
      setData(body); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Dashboard unavailable"); }
    finally { setLoading(false); }
  }, []);
  const syncRing = useCallback(async () => {
    setSyncing(true); setSyncMessage("");
    try {
      const response = await fetch("/api/guardian/ring-sync", { method: "POST" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Ring synchronization failed");
      setSyncMessage(`${body.imported} new event${body.imported === 1 ? "" : "s"} imported · ${body.duplicates} already known`);
      await refresh();
    } catch (cause) {
      setSyncMessage(cause instanceof Error ? cause.message : "Ring synchronization failed");
    } finally { setSyncing(false); }
  }, [refresh]);
  const updateIncident = useCallback(async (action: "acknowledge" | "resolve") => {
    const incident = data?.primaryIncident;
    if (!incident?.incidentId) return;
    setIncidentAction(action); setActionMessage("");
    try {
      const response = await fetch(`/api/guardian/incidents/${encodeURIComponent(incident.incidentId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, resolution: resolutionNote, outcome: resolutionOutcome }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Incident action failed");
      setActionMessage(`${incident.title}: ${action === "acknowledge" ? "acknowledged" : "resolved and recorded"}`);
      setShowResolution(false); setResolutionNote(""); setResolutionOutcome("harmless_activity");
      await refresh();
    } catch (cause) {
      setActionMessage(cause instanceof Error ? cause.message : "Incident action failed");
    } finally { setIncidentAction(""); }
  }, [data?.primaryIncident, refresh, resolutionNote, resolutionOutcome]);
  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 15000); return () => window.clearInterval(timer); }, [refresh]);
  const risk = data?.risk.score ?? 0;
  const apiAvailable = Boolean(data?.api.online) && !error;
  const ringAvailable = apiAvailable && Boolean(data?.ring.online);
  const riskTone = !apiAvailable ? "warning" : risk >= 70 ? "danger" : risk >= 35 || !ringAvailable ? "warning" : "safe";
  const statusTitle = !apiAvailable ? (loading ? "Checking system status" : "Assessment unavailable")
    : risk >= 70 ? "Attention needed" : !ringAvailable ? "Ring connection unavailable"
    : risk >= 35 ? "Review recorded activity" : "No high-risk activity in stored data";
  const statusDescription = !apiAvailable ? "Live status is unknown. Any data below is from the last successful refresh."
    : !ringAvailable ? "Stored incidents remain available, but Ring event access is unavailable. This is not an all-clear."
    : "Assessment reflects stored events, including simulations. Device access alone does not confirm live monitoring.";

  return <main>
    <aside className="sidebar">
      <a className="brand" href="#top"><span className="brand-mark"><Shield/></span><b>Guardian<span>Mesh</span></b></a>
      <nav><a className="active" href="#overview">⌂ <span>Overview</span></a><a href="#incidents">◇ <span>Incidents</span></a><a href="#activity">≋ <span>Activity</span></a><a href="#devices">⌾ <span>Devices</span></a><a href="#privacy">⬡ <span>Privacy</span></a></nav>
      <div className="local-card"><Shield size={20}/><div><strong>Local-first</strong><small>Your data stays under your control.</small></div></div>
      <div className="profile"><div className="avatar">N</div><div><strong>Home Owner</strong><small>Primary administrator</small></div></div>
    </aside>
    <section className="workspace" id="top">
      <header><div className="title"><button className="mobile-brand"><Shield/></button><div><p className="eyebrow">HOME INTELLIGENCE</p><h1>Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}</h1></div></div><div className="header-actions"><div className={`connection ${apiAvailable ? "online" : ""}`}><i/> {apiAvailable ? "Local API online" : loading ? "Connecting" : "API unavailable"}</div><button className="refresh" onClick={() => void refresh()} disabled={loading}>{loading ? "Checking…" : "Refresh"}</button></div></header>
      {error && <div className="error-banner"><strong>Dashboard data unavailable.</strong><span>{error}</span><button onClick={() => void refresh()}>Try again</button></div>}
      <div className="content" id="overview">
        <section className="panel" style={{ marginBottom: 20 }}>
          <PanelHeading eyebrow="SIMULATION ONLY" title="Local demo"><span className="pill">No Ring token needed</span></PanelHeading>
          <p>Synthetic scenarios add labeled events to local history. Scenario timestamps are fixed to daytime or nighttime; scores use demonstration rules.</p>
          <div className="incident-actions">
            {["intrusion", "late_resident", "delivery", "routine"].map(scenario => <button key={scenario} disabled={demoBusy || !apiAvailable} onClick={() => void runDemo(scenario)}>{label(scenario)}</button>)}
          </div>
          <p className="action-message" role="status">{demoBusy ? "Running simulation…" : demoMessage}</p>
          <p>Existing unresolved incidents may keep the main score higher. Resolve a demo incident before starting the next scenario.</p>
        </section>
        <section className="panel baseline-panel" style={{ marginBottom: 20 }}>
          <PanelHeading eyebrow="HOUSEHOLD BASELINE" title="Learning normal, privately"><span className={`pill ${data?.baseline.status === "ready" ? "safe" : "warning"}`}>{data?.baseline.status === "ready" ? "Adaptive mode" : "Learning"}</span></PanelHeading>
          <div className="baseline-grid">
            <div><strong>{data?.baseline.sampleCount ?? 0}</strong><span>confirmed patterns</span></div>
            <div><strong>{Math.round((data?.baseline.confidence ?? 0) * 100)}%</strong><span>baseline confidence</span></div>
            <div><strong>{data?.baseline.activeHours.length ? data.baseline.activeHours.map(hour => `${String(hour).padStart(2,"0")}:00`).join(", ") : "—"}</strong><span>confirmed active hours (UTC)</span></div>
          </div>
          <div className="baseline-progress"><i style={{ width: `${Math.min(100, ((data?.baseline.sampleCount ?? 0) / Math.max(1, data?.baseline.minimumSamples ?? 3)) * 100)}%` }}/></div>
          <p>{data?.baseline.privacy ?? "Waiting for confirmed benign outcomes."}</p>
        </section>
        <section className={`status-hero ${riskTone}`}><div className="hero-copy"><div className="status-kicker"><span><Shield size={18}/></span> GUARDIAN STATUS</div><h2>{statusTitle}</h2><p>{statusDescription}</p><div className="hero-meta"><span><i/> API v{data?.api.version ?? "0.1.0"}</span><span><i/> {ringAvailable ? `${data?.ring.count} Ring device(s) accessible` : "Ring access unavailable"}</span><span><i/> Last loaded {data ? formatTime(data.generatedAt) : "—"}</span></div></div><div className="risk-ring" style={{ "--score": `${risk * 3.6}deg` } as React.CSSProperties}><div><span>{data ? risk : "—"}</span><small>STORED RISK SCORE</small><em>{!apiAvailable ? "Unknown / stale" : label(data?.risk.level ?? "unknown")}</em></div></div></section>
        <section className="stats-grid"><Metric icon="!" tone="red" name="ACTIVE INCIDENTS" value={data?.stats.active ?? "—"} note={!apiAvailable ? "Unknown / stale" : data?.stats.active ? "Review recommended" : "No active stored incidents"}/><Metric icon="≋" tone="blue" name="RECENT SIGNALS" value={data?.stats.signals ?? "—"} note={apiAvailable ? "Stored activity window" : "Unknown / stale"}/><Metric icon="⌾" tone="green" name="CONNECTED DEVICES" value={ringAvailable ? data?.ring.count ?? 0 : "—"} note={ringAvailable ? "Device API reachable" : "Check token and connection"}/></section>
        <div className="dashboard-grid">
          <section className="panel" id="incidents"><PanelHeading eyebrow="PRIORITY VIEW" title="Current assessment"><span className={`pill ${riskTone}`}>{!apiAvailable ? "Unknown / stale" : data?.primaryIncident ? label(data.primaryIncident.status) : "No unresolved incidents"}</span></PanelHeading>{data?.primaryIncident ? <><div className="incident-title"><span className={`metric-icon ${riskTone === "danger" ? "red" : "blue"}`}>!</span><div><h4>{data.primaryIncident.title}</h4><p>{label(data.primaryIncident.severity)} severity · {formatTime(data.primaryIncident.startedAt)}</p><p>{data.primaryIncident.risk.context?.assessment_mode === "adaptive" ? `Adaptive baseline · ${data.primaryIncident.risk.context.baseline_sample_count ?? 0} confirmed patterns` : "Cold-start rules · awaiting confirmed patterns"}</p></div></div><div className="factors">{data.primaryIncident.risk.evidence.slice(0,4).map((factor) => <div className="factor" key={factor.code}><div><strong>{label(factor.code)}</strong><span>+{Math.round(factor.weight * factor.value)}</span></div><p>{factor.explanation}</p><div className="bar"><i style={{width:`${Math.min(100,factor.value*100)}%`}}/></div></div>)}</div><div className="incident-actions"><button onClick={() => void updateIncident("acknowledge")} disabled={!apiAvailable || Boolean(incidentAction) || data.primaryIncident.status === "acknowledged"}>{incidentAction === "acknowledge" ? "Saving…" : data.primaryIncident.status === "acknowledged" ? "Acknowledged" : "Acknowledge"}</button><button className="resolve-button" onClick={() => setShowResolution((visible) => !visible)} disabled={!apiAvailable || Boolean(incidentAction)}>Resolve</button></div>{showResolution && <div className="resolution-form"><label htmlFor="resolution-outcome">What did this activity turn out to be?</label><select id="resolution-outcome" value={resolutionOutcome} onChange={(event) => setResolutionOutcome(event.target.value)}><option value="resident">Resident</option><option value="expected_visitor">Expected visitor</option><option value="delivery">Delivery</option><option value="harmless_activity">Harmless activity</option><option value="suspicious_activity">Suspicious activity</option><option value="unknown">Unknown</option></select><label htmlFor="resolution-note">Resolution note</label><textarea id="resolution-note" value={resolutionNote} onChange={(event) => setResolutionNote(event.target.value)} maxLength={500} placeholder="What happened and how was it handled?"/><div><small>{resolutionNote.length}/500</small><button onClick={() => void updateIncident("resolve")} disabled={!apiAvailable || resolutionNote.trim().length < 3 || Boolean(incidentAction)}>{incidentAction === "resolve" ? "Resolving…" : "Confirm resolution"}</button></div></div>}</> : !apiAvailable ? <div className="empty"><p>Assessment data unavailable.</p></div> : <Empty/>}{actionMessage && <p className="action-message" role="status">{actionMessage}</p>}</section>
          <section className="panel" id="activity"><PanelHeading eyebrow="STORED EVENTS" title="Recent activity"><span className="pill">{apiAvailable ? "Stored history" : "Unknown / stale"}</span></PanelHeading><div className="timeline">{data?.events.length ? data.events.map((event,index)=><div className="timeline-item" key={`${event.occurredAt}-${index}`}><span className="timeline-dot"/><div><strong>{label(event.type)}</strong><p>{event.source}</p></div><time>{formatTime(event.occurredAt)}</time></div>) : <div className="empty compact"><p>No event data available yet.</p></div>}</div></section>
          <section className="panel" id="devices"><PanelHeading eyebrow="INTEGRATIONS" title="Ring connection"><span className={`pill ${ringAvailable ? "safe":"warning"}`}>{ringAvailable ? "API reachable":"Action needed"}</span></PanelHeading><div className="device-body"><div className="device-orbit"><span>◉</span><i/></div><div className="device-copy"><h4>{data?.ring.names[0] ?? "Ring device"}</h4><p>{!apiAvailable ? "Ring status unknown while API data is unavailable." : data?.ring.message}</p><div className="device-tags"><span>Events</span><span>Encrypted</span><span>Local view</span></div><button className="sync-button" onClick={() => void syncRing()} disabled={syncing || !ringAvailable}>{syncing ? "Syncing securely…" : "Sync Ring events"}</button><small className="sync-note">{syncMessage || (data?.ring.sync.lastSyncedAt ? `Last sync ${formatTime(data.ring.sync.lastSyncedAt)} · ${data.ring.sync.imported} imported` : "Not synced yet")}</small></div></div></section>
          <section className="panel" id="privacy"><PanelHeading eyebrow="PRIVACY CENTER" title="Designed to know less"><Shield/></PanelHeading><div className="privacy-list"><Privacy title="Credentials stay server-side" detail="OAuth tokens never enter your browser."/><Privacy title="Device IDs are removed" detail="The dashboard receives only safe summaries."/><Privacy title="Local data store" detail="Incident history remains on your machine."/></div></section>
        </div>
      </div><footer><span>GuardianMesh v0.1.0</span><span>Local command center · Auto-refreshes every 15 seconds</span></footer>
    </section>
  </main>;
}

function Metric({icon,tone,name,value,note}:{icon:string;tone:string;name:string;value:number|string;note:string}) { return <article><span className={`metric-icon ${tone}`}>{icon}</span><div><small>{name}</small><strong>{value}</strong><p>{note}</p></div></article>; }
function PanelHeading({eyebrow,title,children}:{eyebrow:string;title:string;children:React.ReactNode}) { return <div className="panel-heading"><div><p className="eyebrow">{eyebrow}</p><h3>{title}</h3></div>{children}</div>; }
function Privacy({title,detail}:{title:string;detail:string}) { return <div><span>✓</span><p><strong>{title}</strong><small>{detail}</small></p></div>; }
function Empty() { return <div className="empty"><Shield size={36}/><h4>No unresolved incidents</h4><p>Run a simulation or wait for a Ring event. New assessments will appear automatically.</p></div>; }
