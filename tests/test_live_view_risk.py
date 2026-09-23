import unittest
from datetime import datetime

from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import Store


class LiveViewRiskTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.pipeline = GuardianPipeline(self.store)

    def tearDown(self):
        self.store.connection.close()

    def record(self, event_type="on_demand", start=1790181424355, duration=39712):
        return {
            "type": "history-events",
            "id": "test-view-session",
            "attributes": {
                "event_type": event_type, "start": start, "end": start + duration,
                "is_third_party_reviewed": True,
            },
            "relationships": {
                "cv_detections": {"data": []},
                "source": {"data": {"type": "devices", "id": "test-camera"}},
            },
        }

    def test_playground_view_is_stored_without_risk_and_deduplicated(self):
        record = self.record()
        first = self.pipeline.ingest_ring_history(record)
        self.assertEqual(first["risk"]["score"], 0)
        self.assertEqual(first["risk"]["evidence"], [])
        incident = self.store.get_incident(first["incident_id"])
        self.assertEqual(incident["status"], "observed")
        self.assertEqual(incident["severity"], "normal")
        second = self.pipeline.ingest_ring_history(record)
        self.assertTrue(second["duplicate"])
        self.assertEqual(second["event_id"], first["event_id"])
        self.assertEqual(len(self.store.list_events()), 1)
        self.assertEqual(len(self.store.list_incidents()), 1)

    def test_long_nighttime_view_does_not_trigger_time_or_duration_rules(self):
        start = int(datetime.fromisoformat("2026-09-23T02:00:00+00:00").timestamp() * 1000)
        result = self.pipeline.ingest_ring_history(self.record(start=start, duration=600000))
        self.assertEqual(result["risk"]["score"], 0)
        self.assertEqual(result["risk"]["evidence"], [])

    def test_motion_still_receives_duration_factor(self):
        result = self.pipeline.ingest_ring_history(self.record(event_type="motion"))
        factors = {factor["code"]: factor for factor in result["risk"]["evidence"]}
        self.assertIn("PROLONGED_ACTIVITY", factors)
        self.assertGreater(result["risk"]["score"], 0)


if __name__ == "__main__":
    unittest.main()
