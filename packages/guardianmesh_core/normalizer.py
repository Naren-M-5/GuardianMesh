from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import CanonicalEvent

ALLOWED_EVENT_TYPES = {
    "motion.detected", "doorbell.pressed", "person.detected", "animal.detected",
    "vehicle.detected", "device.online", "device.offline", "zone.entered", "zone.exited",
    "live_view.started",
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


def normalize_ring_history(record: dict[str, Any], fallback_device_id: str = "") -> CanonicalEvent:
    """Convert one Ring JSON:API history record into a canonical event."""
    source_event_id = str(record.get("id") or "").strip()
    if not source_event_id:
        raise ValueError("Ring history event requires id")

    attributes = dict(record.get("attributes") or {})
    ring_type = str(attributes.get("event_type") or "").strip().lower()
    base_type, _, subtype = ring_type.partition(".")
    event_types = {
        "motion": "motion.detected",
        "ding": "doorbell.pressed",
        "on_demand": "live_view.started",
    }
    if base_type not in event_types:
        raise ValueError(f"Unsupported Ring history event type: {ring_type}")

    relationships = dict(record.get("relationships") or {})
    source = dict(relationships.get("source") or {})
    source_data = dict(source.get("data") or {})
    device_id = str(source_data.get("id") or fallback_device_id).strip()
    if not device_id:
        raise ValueError("Ring history event requires device id")

    start_ms = attributes.get("start")
    if not isinstance(start_ms, (int, float)):
        raise ValueError("Ring history event requires numeric start timestamp")
    occurred_at = datetime.fromtimestamp(start_ms / 1000, timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    end_ms = attributes.get("end")
    duration = 0.0
    if isinstance(end_ms, (int, float)) and end_ms >= start_ms:
        duration = round((end_ms - start_ms) / 1000, 3)

    labels = {"human": "person", "vehicle": "vehicle", "animal": "animal"}
    label = labels.get(subtype)
    event_type = event_types[base_type]
    if label:
        event_type = f"{label}.detected"

    return CanonicalEvent(
        source="ring",
        source_event_id=source_event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        space_id="space_home_001",
        device_id=device_id,
        zone_id="front_entrance",
        classification={"label": label, "confidence": 1.0 if label else 0.0},
        attributes={
            "duration_seconds": duration,
            "ring_event_type": ring_type,
            "third_party_reviewed": bool(attributes.get("is_third_party_reviewed", False)),
        },
        media={"available": False, "retention": "ephemeral", "reference": None},
        integrity={
            "signature_verified": False,
            "authenticated_source": True,
            "duplicate": False,
        },
    )
