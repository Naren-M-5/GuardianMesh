"""Feedback-trained household activity baselines.

Only events attached to incidents that a homeowner resolved with a benign,
structured outcome are trusted as normal behavior. This keeps an unresolved
or suspicious event from teaching the system that it is routine.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from statistics import median
from typing import Any

BENIGN_OUTCOMES = {"resident", "expected_visitor", "delivery", "harmless_activity"}
RESOLUTION_OUTCOMES = BENIGN_OUTCOMES | {"suspicious_activity", "unknown"}
MIN_BASELINE_SAMPLES = 3


def _hour(value: str) -> int:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).hour


def _duration(event: dict[str, Any]) -> float:
    attributes = event.get("attributes") or {}
    try:
        return max(0.0, float(attributes.get("duration_seconds") or 0))
    except (TypeError, ValueError):
        return 0.0


def pattern_key(event: dict[str, Any]) -> str:
    """A deliberately coarse, non-identifying activity fingerprint."""
    hour_bucket = _hour(str(event["occurred_at"])) // 3
    return "|".join((
        str(event.get("event_type") or "activity"),
        str(event.get("zone_id") or "unknown_zone"),
        str(hour_bucket),
    ))


def build_baseline(space_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [event for event in events if event.get("event_type") != "live_view.started"]
    hours = Counter(_hour(str(event["occurred_at"])) for event in usable)
    zones = Counter(str(event.get("zone_id") or "unknown_zone") for event in usable)
    event_types = Counter(str(event.get("event_type") or "activity") for event in usable)
    patterns = Counter(pattern_key(event) for event in usable)
    durations = [_duration(event) for event in usable if _duration(event) > 0]
    sample_count = len(usable)
    return {
        "space_id": space_id,
        "status": "ready" if sample_count >= MIN_BASELINE_SAMPLES else "learning",
        "sample_count": sample_count,
        "minimum_samples": MIN_BASELINE_SAMPLES,
        "confidence": round(min(1.0, sample_count / 12), 2),
        "active_hours": sorted(hours),
        "usual_zones": [name for name, _ in zones.most_common(5)],
        "event_types": dict(event_types.most_common()),
        "median_duration_seconds": round(float(median(durations)), 1) if durations else 0.0,
        "patterns": dict(patterns),
        "privacy": "Derived only from homeowner-confirmed benign event metadata.",
    }


def circular_hour_distance(hour: int, active_hours: list[int]) -> int:
    if not active_hours:
        return 12
    return min(min(abs(hour - known), 24 - abs(hour - known)) for known in active_hours)
