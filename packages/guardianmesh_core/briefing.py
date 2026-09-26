"""Privacy-safe household briefings derived from stored metadata only."""
from __future__ import annotations

from typing import Any


def build_household_briefing(
    incidents: list[dict[str, Any]], events: list[dict[str, Any]]
) -> dict[str, Any]:
    unresolved = [item for item in incidents if item.get("status") != "resolved"]
    attention = [
        item for item in unresolved
        if int((item.get("risk") or {}).get("score") or 0) >= 40
    ]
    high = [
        item for item in attention
        if int((item.get("risk") or {}).get("score") or 0) >= 70
    ]
    if high:
        state = "attention"
        headline = "A household situation needs review"
        action = "Review the highest-risk situation and confirm what happened."
    elif attention:
        state = "review"
        headline = "Unusual activity should be checked"
        action = "Review the evidence when convenient and label the outcome."
    else:
        state = "quiet"
        headline = "No unresolved high-risk situation"
        action = "No action is suggested from the currently stored metadata."

    notable = sorted(
        unresolved,
        key=lambda item: int((item.get("risk") or {}).get("score") or 0),
        reverse=True,
    )[:3]
    return {
        "state": state,
        "headline": headline,
        "summary": (
            f"GuardianMesh reviewed {len(events)} stored signal"
            f"{'s' if len(events) != 1 else ''} and {len(unresolved)} unresolved situation"
            f"{'s' if len(unresolved) != 1 else ''}."
        ),
        "recommended_action": action,
        "counts": {
            "stored_signals": len(events),
            "unresolved_situations": len(unresolved),
            "attention_situations": len(attention),
        },
        "notable": [
            {
                "title": str(item.get("title") or "Observed activity"),
                "score": int((item.get("risk") or {}).get("score") or 0),
                "level": str((item.get("risk") or {}).get("level") or "normal"),
                "status": str(item.get("status") or "observed"),
            }
            for item in notable
        ],
        "privacy": (
            "Generated from local event metadata and homeowner feedback only; "
            "no video, audio, face identity, or raw device identifier is included."
        ),
        "limitations": (
            "This briefing supports human review and does not confirm safety, identity, "
            "or an emergency."
        ),
    }
