from __future__ import annotations

from datetime import datetime

from .models import CanonicalEvent, RiskAssessment, RiskFactor, new_id


def _risk_factors(event: CanonicalEvent) -> list[RiskFactor]:
    # A viewing session describes use of the camera, not activity in its zone.
    # Keep it in history without treating session length or time as a threat.
    if event.event_type == "live_view.started":
        return []
    hour = datetime.fromisoformat(event.occurred_at.replace("Z", "+00:00")).hour
    factors: list[RiskFactor] = []
    if hour < 5:
        factors.append(RiskFactor("UNUSUAL_TIME", 28, 0.95,
                                  "Activity occurred during a historically inactive period."))
    label = event.classification.get("label")
    confidence = float(event.classification.get("confidence") or 0)
    if event.event_type == "person.detected" or label == "person":
        factors.append(RiskFactor("PERSON_PRESENT", 20, confidence,
                                  "A person was detected in the monitored zone."))
    dwell = float(event.attributes.get("duration_seconds", 0))
    if dwell >= 30:
        factors.append(RiskFactor("PROLONGED_ACTIVITY", 16, min(dwell / 120, 1),
                                  "Activity persisted beyond the normal duration."))
    if bool(event.attributes.get("rare_sequence")):
        factors.append(RiskFactor("RARE_SEQUENCE", 24, 0.9,
                                  "The observed event sequence is uncommon."))
    return factors


def assess(event: CanonicalEvent) -> tuple[RiskAssessment, dict]:
    factors = _risk_factors(event)
    score = min(100, sum(round(f.weight * f.value) for f in factors))
    level = "high" if score >= 70 else "suspicious" if score >= 40 else "watch" if score >= 20 else "normal"
    incident_id = new_id("inc")
    risk = RiskAssessment(incident_id, score, level, factors,
                          round(sum(f.value for f in factors) / len(factors), 2) if factors else 1.0)
    incident = {
        "incident_id": incident_id, "space_id": event.space_id,
        "type": "suspicious_access" if score >= 40 else "activity",
        "status": "active" if score >= 40 else "observed", "severity": level,
        "title": "Unexpected entrance activity" if score >= 40 else "Routine activity",
        "started_at": event.occurred_at, "updated_at": event.received_at,
        "evidence_events": [event.event_id], "resolution": None,
    }
    return risk, incident
