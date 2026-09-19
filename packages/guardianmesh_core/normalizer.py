from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import CanonicalEvent

ALLOWED_EVENT_TYPES = {
    "motion.detected", "doorbell.pressed", "person.detected", "animal.detected",
    "vehicle.detected", "device.online", "device.offline", "zone.entered", "zone.exited",
}


def _iso(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_ring(payload: dict[str, Any], signature_verified: bool) -> CanonicalEvent:
    source_event_id = str(payload.get("id") or payload.get("event_id") or "").strip()
    if not source_event_id:
        raise ValueError("Ring event requires id")
    event_type = str(payload.get("type") or payload.get("event_type") or "").strip()
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"Unsupported event type: {event_type}")
    classification = payload.get("classification") or {}
    return CanonicalEvent(
        source="ring",
        source_event_id=source_event_id,
        event_type=event_type,
        occurred_at=_iso(payload.get("occurred_at") or payload.get("timestamp")),
        space_id=str(payload.get("space_id") or "space_home_001"),
        device_id=str(payload.get("device_id") or "ring_frontdoor_001"),
        zone_id=str(payload.get("zone_id") or "front_entrance"),
        classification={
            "label": classification.get("label"),
            "confidence": float(classification.get("confidence", 0.0)),
        },
        attributes=dict(payload.get("attributes") or {}),
        media={"available": bool(payload.get("media_available", False)),
               "retention": "ephemeral", "reference": None},
        integrity={"signature_verified": signature_verified, "duplicate": False},
    )
