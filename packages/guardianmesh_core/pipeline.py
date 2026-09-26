from typing import Any

from .models import CanonicalEvent
from .normalizer import normalize_ring, normalize_ring_history
from .risk import assess
from .situation import assess_situation
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
        baseline = self.store.get_baseline(persisted.space_id)
        candidate = None
        if persisted.source == "ring" and persisted.event_type != "live_view.started":
            candidate = self.store.find_correlatable_incident(persisted)
        if candidate:
            events = self.store.get_events_by_ids(candidate["evidence_events"]) + [persisted]
            risk, incident = assess_situation(events, baseline, candidate["incident_id"])
        else:
            risk, incident = assess(persisted, baseline)
        self.store.add_incident(incident, risk)
        return {
            "accepted": True, "duplicate": False, "event_id": persisted.event_id,
            "incident_id": incident["incident_id"], "risk": risk.to_dict(),
        }
