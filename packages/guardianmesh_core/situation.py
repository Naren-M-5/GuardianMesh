"""Correlate nearby signals into one explainable, evolving situation."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .baseline import pattern_key
from .models import CanonicalEvent, RiskAssessment, RiskFactor, new_id
from .risk import _risk_factors

CORRELATION_WINDOW_SECONDS = 300


def _time(event: CanonicalEvent) -> datetime:
    return datetime.fromisoformat(event.occurred_at.replace("Z", "+00:00"))


def assess_situation(
    events: list[CanonicalEvent], baseline: dict[str, Any] | None = None,
    incident_id: str | None = None,
) -> tuple[RiskAssessment, dict[str, Any]]:
    if not events:
        raise ValueError("A situation requires at least one event")
    ordered = sorted(events, key=_time)
    baseline = baseline or {}

    strongest: dict[str, RiskFactor] = {}
    for event in ordered:
        for factor in _risk_factors(event, baseline):
            previous = strongest.get(factor.code)
            if previous is None or factor.weight * factor.value > previous.weight * previous.value:
                strongest[factor.code] = factor

    activity_events = [event for event in ordered if event.event_type != "live_view.started"]
    if len(activity_events) >= 3:
        strongest["REPEATED_ACTIVITY"] = RiskFactor(
            "REPEATED_ACTIVITY", 18, min(1.0, len(activity_events) / 5),
            f"{len(activity_events)} related signals occurred within five minutes.",
        )

    types = [event.event_type for event in activity_events]
    doorbell_index = next((index for index, value in enumerate(types) if value == "doorbell.pressed"), None)
    person_index = next((index for index, value in enumerate(types) if value == "person.detected"), None)
    expected_arrival = (
        doorbell_index is not None and person_index is not None and doorbell_index < person_index
    )

    latest = ordered[-1]
    known_count = int((baseline.get("patterns") or {}).get(pattern_key(latest.to_dict()), 0))
    familiarity_adjustment = -12 if baseline.get("status") == "ready" and known_count >= 2 else 0
    expected_adjustment = -12 if expected_arrival else 0
    factors = list(strongest.values())
    base_score = sum(round(factor.weight * factor.value) for factor in factors)
    score = max(0, min(100, base_score + familiarity_adjustment + expected_adjustment))
    level = "high" if score >= 70 else "suspicious" if score >= 40 else "watch" if score >= 20 else "normal"
    stable_incident_id = incident_id or new_id("inc")
    context = {
        "assessment_mode": "adaptive" if baseline.get("status") == "ready" else "cold_start",
        "baseline_sample_count": int(baseline.get("sample_count") or 0),
        "baseline_confidence": float(baseline.get("confidence") or 0),
        "known_pattern_count": known_count,
        "familiarity_adjustment": familiarity_adjustment,
        "expected_sequence_adjustment": expected_adjustment,
        "event_count": len(ordered),
        "sequence": types,
        "correlation_window_seconds": CORRELATION_WINDOW_SECONDS,
    }
    confidence = round(sum(factor.value for factor in factors) / len(factors), 2) if factors else 1.0
    risk = RiskAssessment(stable_incident_id, score, level, factors, confidence, context)
    incident = {
        "incident_id": stable_incident_id,
        "space_id": latest.space_id,
        "type": "suspicious_access" if score >= 40 else "activity",
        "status": "active" if score >= 40 else "observed",
        "severity": level,
        "title": "Evolving entrance activity" if len(ordered) > 1 else (
            "Unexpected entrance activity" if score >= 40 else "Routine activity"
        ),
        "started_at": ordered[0].occurred_at,
        "updated_at": latest.received_at,
        "evidence_events": [event.event_id for event in ordered],
        "resolution": None,
    }
    return risk, incident
