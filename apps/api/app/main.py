from __future__ import annotations

import json

from fastapi import FastAPI, Header, HTTPException, Query, Request

from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.policy import authorize
from packages.guardianmesh_core.signing import SignatureError, verify
from packages.guardianmesh_core.storage import Store

from .config import settings

app = FastAPI(title="GuardianMesh API", version="0.1.0")
store = Store(settings.db_path)
pipeline = GuardianPipeline(store)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "healthy", "version": "0.1.0"}


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


@app.get("/api/v1/events")
def list_events(space_id: str | None = None, limit: int = Query(100, ge=1, le=500)) -> dict:
    return {"items": store.list_events(space_id, limit)}


@app.get("/api/v1/incidents")
def list_incidents(limit: int = Query(100, ge=1, le=500)) -> dict:
    return {"items": store.list_incidents(limit)}


@app.get("/api/v1/incidents/{incident_id}")
def get_incident(incident_id: str) -> dict:
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/api/v1/incidents/{incident_id}/explanation")
def explain_incident(incident_id: str) -> dict:
    incident = store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    risk = incident["risk"]
    return {
        "incident_id": incident_id, "risk_score": risk["score"],
        "summary": incident["title"],
        "factors": [{"factor": x["code"].lower(), "contribution": round(x["weight"] * x["value"])}
                    for x in risk["evidence"]],
        "evidence": incident["evidence_events"],
    }


@app.get("/api/v1/policy/{action}")
def policy_check(action: str) -> dict:
    result = authorize(action)
    return {"action": action, "decision": result.decision, "reason": result.reason}
