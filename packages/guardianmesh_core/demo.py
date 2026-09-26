"""Local, synthetic scenarios. No Ring API calls or physical device actions."""
from datetime import datetime, timezone
from uuid import uuid4

from .normalizer import normalize_ring
from .risk import assess
from .storage import Store


def run_demo(store: Store, scenario: str) -> dict:
    if scenario not in {"intrusion", "late_resident", "delivery", "routine"}:
        raise ValueError("Unknown demo scenario")
    intrusion = scenario == "intrusion"
    person = scenario != "routine"
    # Fixed scenario hour makes results repeatable, independent of demo time.
    occurred = datetime.now(timezone.utc).replace(
        hour=2 if scenario in {"intrusion", "late_resident"} else 12,
        minute=0, second=0, microsecond=0
    ).isoformat()
    event = normalize_ring({
        "id": f"demo_{uuid4().hex}", "simulation": True,
        "type": "person.detected" if person else "motion.detected",
        "occurred_at": occurred, "device_id": "local_demo_device",
        "space_id": "space_demo",
        "zone_id": "restricted_side_entrance" if intrusion else "demo_entrance",
        "classification": {"label": "person" if person else "motion",
                           "confidence": 0.96 if intrusion else 0.95},
        "attributes": {"duration_seconds": 74 if intrusion else 12 if person else 4,
                       "rare_sequence": intrusion, "demo_scenario": scenario},
    }, False)
    event.source = "simulation"
    event.integrity["ingestion_method"] = "local_demo"
    persisted, _ = store.add_event(event)
    risk, incident = assess(persisted, store.get_baseline(persisted.space_id))
    incident["title"] = f"Simulation: {scenario.title()}"
    store.add_incident(incident, risk)
    return {"scenario": scenario, "simulation": True, "incident_id": incident["incident_id"],
            "risk": risk.to_dict()}
