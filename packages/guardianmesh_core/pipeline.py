from typing import Any

from .models import CanonicalEvent
from .normalizer import normalize_ring, normalize_ring_history
from .risk import assess
from .storage import Store


class GuardianPipeline:
    def __init__(self, store: Store):
        self.store = store

    def ingest_ring(self, payload: dict[str, Any], signature_verified: bool) -> dict[str, Any]:
        event = normalize_ring(payload, signature_verified)
        return self._persist(event)

    def ingest_ring_history(self, record: dict[str, Any], device_id: str = "") -> dict[str, Any]:
        event = normalize_ring_history(record, device_id)
        return self._persist(event)

    def _persist(self, event: CanonicalEvent) -> dict[str, Any]:
        persisted, created = self.store.add_event(event)
        if not created:
            return {"accepted": True, "duplicate": True, "event_id": persisted.event_id}
        risk, incident = assess(persisted, self.store.get_baseline(persisted.space_id))
        self.store.add_incident(incident, risk)
        return {
            "accepted": True, "duplicate": False, "event_id": persisted.event_id,
            "incident_id": incident["incident_id"], "risk": risk.to_dict(),
        }
