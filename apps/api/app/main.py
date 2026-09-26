from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.policy import authorize
from packages.guardianmesh_core.signing import SignatureError, verify
from packages.guardianmesh_core.storage import InvalidIncidentTransition, Store

from .config import settings
from packages.guardianmesh_core.demo import run_demo, run_situation_demo
from packages.guardianmesh_core.explanation import explain_incident as build_explanation
from .ring_client import (
    RingApiError,
    list_device_events,
    list_devices as ring_list_devices,
)

app = FastAPI(title="GuardianMesh API", version="0.1.0")
store = Store(settings.db_path)
pipeline = GuardianPipeline(store)


class ResolveIncidentRequest(BaseModel):
    resolution: str = Field(min_length=3, max_length=500)
    outcome: Literal[
        "resident", "expected_visitor", "delivery", "harmless_activity",
        "suspicious_activity", "unknown",
    ] = "unknown"


def require_local(request: Request) -> None:
    client_host = request.client.host if request.client else ""
    if client_host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(
            status_code=403,
            detail="Ring integration controls are available only from this laptop.",
        )


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/v1/demo/{scenario}")
def demo_scenario(scenario: str, request: Request) -> dict:
    require_local(request)
    origin = request.headers.get("origin")
    if origin and origin not in {"http://localhost:3000", "http://127.0.0.1:3000"}:
        raise HTTPException(status_code=403, detail="Local demo only")
    try:
        return run_demo(store, scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/demo/situation/{scenario}")
def demo_situation(scenario: str, request: Request) -> dict:
    require_local(request)
    origin = request.headers.get("origin")
    if origin and origin not in {"http://localhost:3000", "http://127.0.0.1:3000"}:
        raise HTTPException(status_code=403, detail="Local demo only")
    try:
        return run_situation_demo(pipeline, scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/integrations/ring/webhook", status_code=202)
async def ring_webhook(
    request: Request,
    x_ring_timestamp: str | None = Header(default=None),
    x_ring_signature: str | None = Header(default=None),
) -> dict:
    body = await request.body()
    signature_verified = False
    if not settings.allow_unsigned_simulator:
        try:
            verify(body, settings.webhook_secret, x_ring_timestamp, x_ring_signature)
            signature_verified = True
        except SignatureError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
    try:
        payload = json.loads(body)
        return pipeline.ingest_ring(payload, signature_verified)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/integrations/ring/devices")
def get_ring_devices(request: Request) -> dict:
    """Discover Ring devices using a token stored only in local .env."""
    require_local(request)
    try:
        return ring_list_devices(settings.ring_access_token, settings.ring_api_base_url)
    except RingApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/integrations/ring/sync/status")
def get_ring_sync_status(request: Request) -> dict:
    require_local(request)
    return store.get_integration_state("ring") or {
        "status": "never_synced",
        "last_synced_at": None,
        "fetched": 0,
        "imported": 0,
        "duplicates": 0,
    }


@app.post("/api/v1/integrations/ring/sync")
def sync_ring_events(request: Request) -> dict:
    """Import the newest Ring history page for every authorized device."""
    require_local(request)
    try:
        devices_payload = ring_list_devices(
            settings.ring_access_token, settings.ring_api_base_url
        )
        devices = devices_payload.get("data") or []
        fetched = imported = duplicates = skipped = 0
        for device in devices:
            if not isinstance(device, dict):
                skipped += 1
                continue
            device_id = str(device.get("id") or "").strip()
            if not device_id:
                skipped += 1
                continue
            history = list_device_events(
                settings.ring_access_token,
                device_id,
                settings.ring_api_base_url,
            )
            for record in history.get("data") or []:
                fetched += 1
                try:
                    result = pipeline.ingest_ring_history(record, device_id)
                    if result["duplicate"]:
                        duplicates += 1
                    else:
                        imported += 1
                except ValueError:
                    skipped += 1

        state = {
            "status": "ok",
            "last_synced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "devices": len(devices),
            "fetched": fetched,
            "imported": imported,
            "duplicates": duplicates,
            "skipped": skipped,
        }
        store.set_integration_state("ring", state)
        return state
    except RingApiError as exc:
        state = {
            "status": "error",
            "last_synced_at": None,
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "message": str(exc),
        }
        store.set_integration_state("ring", state)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/events")
def list_events(space_id: str | None = None, limit: int = Query(100, ge=1, le=500)) -> dict:
    return {"items": store.list_events(space_id, limit)}


@app.get("/api/v1/incidents")
def list_incidents(limit: int = Query(100, ge=1, le=500)) -> dict:
    return {"items": store.list_incidents(limit)}


@app.get("/api/v1/baselines")
def list_household_baselines() -> dict:
    """Profiles contain confirmed metadata patterns, never media or identities."""
    return {"items": store.list_baselines()}


@app.get("/api/v1/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict:
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.post("/api/v1/incidents/{incident_id}/acknowledge")
def acknowledge_incident(incident_id: str, request: Request) -> dict:
    require_local(request)
    try:
        incident = store.transition_incident(
            incident_id, "acknowledged", actor="local_home_owner"
        )
    except InvalidIncidentTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.post("/api/v1/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: str, payload: ResolveIncidentRequest, request: Request
) -> dict:
    require_local(request)
    try:
        incident = store.transition_incident(
            incident_id,
            "resolved",
            actor="local_home_owner",
            resolution=payload.resolution,
            resolution_outcome=payload.outcome,
        )
    except InvalidIncidentTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/api/v1/incidents/{incident_id}/audit")
def incident_audit(
    incident_id: str, request: Request, limit: int = Query(50, ge=1, le=100)
) -> dict:
    require_local(request)
    if not store.get_incident(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"items": store.list_incident_audit(incident_id, limit)}


@app.get("/api/v1/incidents/{incident_id}/explanation")
def explain_incident(incident_id: str) -> dict:
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    events = [event.to_dict() for event in store.get_events_by_ids(incident["evidence_events"])]
    return build_explanation(incident, events)


@app.get("/api/v1/policy/{action}")
def policy_check(action: str) -> dict:
    result = authorize(action)
    return {"action": action, "decision": result.decision, "reason": result.reason}
