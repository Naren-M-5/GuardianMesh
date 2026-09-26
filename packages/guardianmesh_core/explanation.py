"""Evidence-grounded incident explanations with deterministic counterfactuals."""
from __future__ import annotations

from typing import Any


def explain_incident(incident: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    risk = incident["risk"]
    factors = risk.get("evidence") or []
    context = risk.get("context") or {}
    contributions = [
        {
            "code": str(factor.get("code") or "SIGNAL"),
            "contribution": round(float(factor.get("weight") or 0) * float(factor.get("value") or 0)),
            "explanation": str(factor.get("explanation") or "Observed evidence."),
        }
        for factor in factors
    ]
    evidence_total = sum(item["contribution"] for item in contributions)
    adjustments = {
        "familiarity": int(context.get("familiarity_adjustment") or 0),
        "expected_sequence": int(context.get("expected_sequence_adjustment") or 0),
    }
    adjustment_total = sum(adjustments.values())
    score = int(risk.get("score") or 0)
    ordered_types = list(context.get("sequence") or [event.get("event_type") for event in events])
    event_count = int(context.get("event_count") or len(events))

    strongest = sorted(contributions, key=lambda item: item["contribution"], reverse=True)
    reason_text = "; ".join(item["explanation"].rstrip(".") for item in strongest[:3])
    narrative = (
        f"GuardianMesh assessed {event_count} related signal{'s' if event_count != 1 else ''} "
        f"as {risk.get('level', 'unknown')} risk with score {score}."
    )
    if reason_text:
        narrative += f" The strongest evidence was: {reason_text}."
    if adjustment_total < 0:
        narrative += f" Confirmed context reduced the result by {abs(adjustment_total)} points."

    counterfactuals = [
        {
            "without": item["code"],
            "score": max(0, score - item["contribution"]),
            "change": -item["contribution"],
        }
        for item in strongest if item["contribution"] > 0
    ]
    return {
        "incident_id": incident["incident_id"],
        "summary": incident["title"],
        "narrative": narrative,
        "score": score,
        "level": risk.get("level", "unknown"),
        "calculation": {
            "evidence_total": evidence_total,
            "adjustments": adjustments,
            "final_score": score,
        },
        "factors": contributions,
        "situation": {
            "event_count": event_count,
            "sequence": ordered_types,
            "assessment_mode": context.get("assessment_mode", "cold_start"),
            "baseline_sample_count": int(context.get("baseline_sample_count") or 0),
        },
        "counterfactuals": counterfactuals,
        "evidence_event_count": len(events),
        "grounding": "Generated only from stored event metadata and deterministic risk evidence.",
        "limitations": "This assessment does not identify a person or confirm an emergency.",
    }
