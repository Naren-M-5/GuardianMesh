from __future__ import annotations

from datetime import datetime

from .models import CanonicalEvent, RiskAssessment, RiskFactor, new_id
from .baseline import circular_hour_distance, pattern_key


def _risk_factors(event: CanonicalEvent, baseline: dict | None = None) -> list[RiskFactor]:
    # A viewing session describes use of the camera, not activity in its zone.
    # Keep it in history without treating session length or time as a threat.
    if event.event_type == "live_view.started":
        return []
    hour = datetime.fromisoformat(event.occurred_at.replace("Z", "+00:00")).hour
    factors: list[RiskFactor] = []
    ready = bool(baseline and baseline.get("status") == "ready")
    if ready:
        distance = circular_hour_distance(hour, list(baseline.get("active_hours") or []))
        if distance >= 4:
            factors.append(RiskFactor(
                "BASELINE_TIME_DEVIATION", 28, min(0.95, 0.55 + distance * 0.08),
                f"Activity was {distance} hours from this household's confirmed active periods.",
            ))
        usual_zones = set(baseline.get("usual_zones") or [])
        if usual_zones and event.zone_id not in usual_zones:
            factors.append(RiskFactor(
                "BASELINE_ZONE_DEVIATION", 28, 0.95,
                "Activity occurred in a zone absent from confirmed household patterns.",
            ))
    elif hour < 5:
        factors.append(RiskFactor("UNUSUAL_TIME", 28, 0.95,
                                  "Activity occurred during the cold-start quiet period."))
    label = event.classification.get("label")
    confidence = float(event.classification.get("confidence") or 0)
    if event.event_type == "person.detected" or label == "person":
        factors.append(RiskFactor("PERSON_PRESENT", 20, confidence,
                                  "A person was detected in the monitored zone."))
    dwell = float(event.attributes.get("duration_seconds", 0))
    median_duration = float((baseline or {}).get("median_duration_seconds") or 0)
    duration_threshold = max(30.0, median_duration * 2) if ready else 30.0
    if dwell >= duration_threshold:
        explanation = (
            f"Activity lasted {round(dwell)} seconds versus a confirmed median of "
            f"{round(median_duration)} seconds."
            if ready and median_duration else "Activity persisted beyond the cold-start duration threshold."
        )
        factors.append(RiskFactor("PROLONGED_ACTIVITY", 16, min(dwell / 120, 1), explanation))
    if bool(event.attributes.get("rare_sequence")):
        factors.append(RiskFactor("RARE_SEQUENCE", 24, 0.9,
                                  "The observed event sequence is uncommon."))
    return factors


def assess(event: CanonicalEvent, baseline: dict | None = None) -> tuple[RiskAssessment, dict]:
    baseline = baseline or {}
    factors = _risk_factors(event, baseline)
    base_score = sum(round(f.weight * f.value) for f in factors)
    event_data = event.to_dict()
    known_pattern_count = int((baseline.get("patterns") or {}).get(pattern_key(event_data), 0))
    familiarity_adjustment = -12 if baseline.get("status") == "ready" and known_pattern_count >= 2 else 0
    score = max(0, min(100, base_score + familiarity_adjustment))
    level = "high" if score >= 70 else "suspicious" if score >= 40 else "watch" if score >= 20 else "normal"
    incident_id = new_id("inc")
    context = {
        "assessment_mode": "adaptive" if baseline.get("status") == "ready" else "cold_start",
        "baseline_sample_count": int(baseline.get("sample_count") or 0),
        "baseline_confidence": float(baseline.get("confidence") or 0),
        "known_pattern_count": known_pattern_count,
        "familiarity_adjustment": familiarity_adjustment,
    }
    risk = RiskAssessment(
        incident_id, score, level, factors,
        round(sum(f.value for f in factors) / len(factors), 2) if factors else 1.0,
        context,
    )
    incident = {
        "incident_id": incident_id, "space_id": event.space_id,
        "type": "suspicious_access" if score >= 40 else "activity",
        "status": "active" if score >= 40 else "observed", "severity": level,
        "title": "Unexpected entrance activity" if score >= 40 else "Routine activity",
        "started_at": event.occurred_at, "updated_at": event.received_at,
        "evidence_events": [event.event_id], "resolution": None,
    }
    return risk, incident
