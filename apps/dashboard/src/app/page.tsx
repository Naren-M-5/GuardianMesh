"use client";

import { useCallback, useEffect, useState } from "react";

type Factor = { code: string; weight: number; value: number; explanation: string };
type Incident = { title: string; severity: string; status: string; startedAt: string; risk: { score: number; level: string; evidence: Factor[] } };
type Overview = {
  generatedAt: string; api: { online: boolean; version: string };
  ring: { online: boolean; count: number; names: string[]; message: string };
  risk: { score: number; level: string; evidence: Factor[] }; primaryIncident: Incident | null;
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
  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/guardian/overview", { cache: "no-store" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? body.error ?? "Dashboard unavailable");
      setData(body); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Dashboard unavailable"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 15000); return () => window.clearInterval(timer); }, [refresh]);
  const risk = data?.risk.score ?? 0;
  const riskTone = risk >= 70 ? "danger" : risk >= 35 ? "warning" : "safe";

  return <main>
    <aside className="sidebar">
      <a className="brand" href="#top"><span className="brand-mark"><Shield/></span><b>Guardian<span>Mesh</span></b></a>
      <nav><a className="active" href="#overview">⌂ <span>Overview</span></a><a href="#incidents">◇ <span>Incidents</span></a><a href="#activity">≋ <span>Activity</span></a><a href="#devices">⌾ <span>Devices</span></a><a href="#privacy">⬡ <span>Privacy</span></a></nav>
      <div className="local-card"><Shield size={20}/><div><strong>Local-first</strong><small>Your data stays under your control.</small></div></div>
      <div className="profile"><div className="avatar">N</div><div><strong>Home Owner</strong><small>Primary administrator</small></div></div>
    </aside>
    <section className="workspace" id="top">
      <header><div className="title"><button className="mobile-brand"><Shield/></button><div><p className="eyebrow">HOME INTELLIGENCE</p><h1>Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}</h1></div></div><div className="header-actions"><div className={`connection ${data?.api.online ? "online" : ""}`}><i/> {data?.api.online ? "System online" : "Connecting"}</div><button className="refresh" onClick={() => void refresh()} disabled={loading}>{loading ? "Checking…" : "Refresh"}</button></div></header>
      {error && <div className="error-banner"><strong>Dashboard cannot reach the API.</strong><span>{error}</span><button onClick={() => void refresh()}>Try again</button></div>}
      <div className="content" id="overview">
        <section className={`status-hero ${riskTone}`}><div className="hero-copy"><div className="status-kicker"><span><Shield size={18}/></span> GUARDIAN STATUS</div><h2>{risk >= 70 ? "Attention needed" : risk >= 35 ? "Monitoring activity" : "Your home is protected"}</h2><p>{risk >= 70 ? "GuardianMesh detected a high-confidence event. Review the evidence below." : "GuardianMesh is watching the signals that matter and keeping routine activity quiet."}</p><div className="hero-meta"><span><i/> API v{data?.api.version ?? "0.1.0"}</span><span><i/> {data?.ring.online ? `${data.ring.count} Ring device${data.ring.count === 1 ? "" : "s"}` : "Ring token needs refresh"}</span><span><i/> Updated {data ? formatTime(data.generatedAt) : "now"}</span></div></div><div className="risk-ring" style={{ "--score": `${risk * 3.6}deg` } as React.CSSProperties}><div><span>{risk}</span><small>RISK SCORE</small><em>{label(data?.risk.level ?? "normal")}</em></div></div></section>
        <section className="stats-grid"><Metric icon="!" tone="red" name="ACTIVE INCIDENTS" value={data?.stats.active ?? 0} note={data?.stats.active ? "Review recommended" : "No open alerts"}/><Metric icon="≋" tone="blue" name="RECENT SIGNALS" value={data?.stats.signals ?? 0} note="Latest activity window"/><Metric icon="⌾" tone="green" name="CONNECTED DEVICES" value={data?.ring.count ?? 0} note={data?.ring.online ? "Ring connection healthy" : "Refresh OAuth token"}/></section>
        <div className="dashboard-grid">
          <section className="panel" id="incidents"><PanelHeading eyebrow="PRIORITY VIEW" title="Current assessment"><span className={`pill ${riskTone}`}>{data?.primaryIncident ? label(data.primaryIncident.status) : "All clear"}</span></PanelHeading>{data?.primaryIncident ? <><div className="incident-title"><span className={`metric-icon ${riskTone === "danger" ? "red" : "blue"}`}>!</span><div><h4>{data.primaryIncident.title}</h4><p>{label(data.primaryIncident.severity)} severity · {formatTime(data.primaryIncident.startedAt)}</p></div></div><div className="factors">{data.primaryIncident.risk.evidence.slice(0,4).map((factor) => <div className="factor" key={factor.code}><div><strong>{label(factor.code)}</strong><span>+{Math.round(factor.weight * factor.value)}</span></div><p>{factor.explanation}</p><div className="bar"><i style={{width:`${Math.min(100,factor.value*100)}%`}}/></div></div>)}</div></> : <Empty/>}</section>
          <section className="panel" id="activity"><PanelHeading eyebrow="LIVE FEED" title="Recent activity"><span className="live-dot">LIVE</span></PanelHeading><div className="timeline">{data?.events.length ? data.events.map((event,index)=><div className="timeline-item" key={`${event.occurredAt}-${index}`}><span className="timeline-dot"/><div><strong>{label(event.type)}</strong><p>{event.source} signal processed</p></div><time>{formatTime(event.occurredAt)}</time></div>) : <div className="empty compact"><p>No event data available yet.</p></div>}</div></section>
          <section className="panel" id="devices"><PanelHeading eyebrow="INTEGRATIONS" title="Ring connection"><span className={`pill ${data?.ring.online ? "safe":"warning"}`}>{data?.ring.online ? "Connected":"Action needed"}</span></PanelHeading><div className="device-body"><div className="device-orbit"><span>◉</span><i/></div><div><h4>{data?.ring.names[0] ?? "Ring device"}</h4><p>{data?.ring.message ?? "Checking secure connection…"}</p><div className="device-tags"><span>Events</span><span>Encrypted</span><span>Local view</span></div></div></div></section>
          <section className="panel" id="privacy"><PanelHeading eyebrow="PRIVACY CENTER" title="Designed to know less"><Shield/></PanelHeading><div className="privacy-list"><Privacy title="Credentials stay server-side" detail="OAuth tokens never enter your browser."/><Privacy title="Device IDs are removed" detail="The dashboard receives only safe summaries."/><Privacy title="Local data store" detail="Incident history remains on your machine."/></div></section>
        </div>
      </div><footer><span>GuardianMesh v0.1.0</span><span>Local command center · Auto-refreshes every 15 seconds</span></footer>
    </section>
  </main>;
}

function Metric({icon,tone,name,value,note}:{icon:string;tone:string;name:string;value:number;note:string}) { return <article><span className={`metric-icon ${tone}`}>{icon}</span><div><small>{name}</small><strong>{value}</strong><p>{note}</p></div></article>; }
function PanelHeading({eyebrow,title,children}:{eyebrow:string;title:string;children:React.ReactNode}) { return <div className="panel-heading"><div><p className="eyebrow">{eyebrow}</p><h3>{title}</h3></div>{children}</div>; }
function Privacy({title,detail}:{title:string;detail:string}) { return <div><span>✓</span><p><strong>{title}</strong><small>{detail}</small></p></div>; }
function Empty() { return <div className="empty"><Shield size={36}/><h4>No incidents yet</h4><p>Run a simulation or wait for a Ring event. New assessments will appear automatically.</p></div>; }
