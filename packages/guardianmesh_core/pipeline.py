from typing import Any

from .models import CanonicalEvent
from .normalizer import normalize_ring
from .risk import assess
from .storage import Store


class GuardianPipeline:
    def __init__(self, store: Store):
        self.store = store

    def ingest_ring(self, payload: dict[str, Any], signature_verified: bool) -> dict[str, Any]:
        event = normalize_ring(payload, signature_verified)
        persisted, created = self.store.add_event(event)
        if not created:
            return {"accepted": True, "duplicate": True, "event_id": persisted.event_id}
        risk, incident = assess(persisted)
        self.store.add_incident(incident, risk)
        return {
            "accepted": True, "duplicate": False, "event_id": persisted.event_id,
            "incident_id": incident["incident_id"], "risk": risk.to_dict(),
        }
