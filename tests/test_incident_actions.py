import unittest

from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import InvalidIncidentTransition, Store


class IncidentActionTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.pipeline = GuardianPipeline(self.store)
        result = self.pipeline.ingest_ring(
            {
                "id": "incident_action_event",
                "type": "person.detected",
                "occurred_at": "2026-09-19T02:13:08Z",
                "space_id": "space_test",
                "device_id": "ring_front",
                "zone_id": "entrance",
                "classification": {"label": "person", "confidence": 0.96},
                "attributes": {"duration_seconds": 74, "rare_sequence": True},
            },
            True,
        )
        self.incident_id = result["incident_id"]

    def test_acknowledge_then_resolve_records_audit_history(self):
        acknowledged = self.store.transition_incident(
            self.incident_id, "acknowledged", actor="local_home_owner"
        )
        self.assertEqual(acknowledged["status"], "acknowledged")

        resolved = self.store.transition_incident(
            self.incident_id,
            "resolved",
            actor="local_home_owner",
            resolution="Confirmed household member; no action required.",
        )
        self.assertEqual(resolved["status"], "resolved")
        self.assertEqual(
            resolved["resolution"], "Confirmed household member; no action required."
        )

        audit = self.store.list_incident_audit(self.incident_id)
        self.assertEqual([item["action"] for item in audit], [
            "incident.resolved",
            "incident.acknowledged",
        ])
        self.assertEqual(audit[0]["details"]["from_status"], "acknowledged")

    def test_resolve_requires_note(self):
        with self.assertRaisesRegex(InvalidIncidentTransition, "resolution note"):
            self.store.transition_incident(
                self.incident_id, "resolved", actor="local_home_owner", resolution="  "
            )

    def test_resolved_incident_cannot_transition_again(self):
        self.store.transition_incident(
            self.incident_id,
            "resolved",
            actor="local_home_owner",
            resolution="Reviewed and closed.",
        )
        with self.assertRaisesRegex(InvalidIncidentTransition, "cannot change"):
            self.store.transition_incident(
                self.incident_id, "acknowledged", actor="local_home_owner"
            )

    def test_missing_incident_returns_none(self):
        self.assertIsNone(
            self.store.transition_incident(
                "inc_missing", "acknowledged", actor="local_home_owner"
            )
        )


if __name__ == "__main__":
    unittest.main()
