import unittest

from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import Store
from packages.guardianmesh_core.demo import run_situation_demo


class SituationCorrelationTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.pipeline = GuardianPipeline(self.store)

    def tearDown(self):
        self.store.connection.close()

    def event(self, event_id, event_type, minute, *, duration=0, rare=False, hour=2):
        label = "person" if event_type == "person.detected" else None
        return {
            "id": event_id, "type": event_type,
            "occurred_at": f"2026-09-20T{hour:02d}:{minute:02d}:00Z",
            "space_id": "home", "device_id": "front", "zone_id": "entrance",
            "classification": {"label": label, "confidence": 0.96 if label else 0},
            "attributes": {"duration_seconds": duration, "rare_sequence": rare},
        }

    def test_related_signals_escalate_one_incident(self):
        first = self.pipeline.ingest_ring(self.event("motion-1", "motion.detected", 0), True)
        second = self.pipeline.ingest_ring(self.event("person-1", "person.detected", 1), True)
        third = self.pipeline.ingest_ring(
            self.event("motion-2", "motion.detected", 2, duration=74, rare=True), True
        )

        self.assertEqual(first["incident_id"], second["incident_id"])
        self.assertEqual(second["incident_id"], third["incident_id"])
        self.assertLess(first["risk"]["score"], second["risk"]["score"])
        self.assertLess(second["risk"]["score"], third["risk"]["score"])
        self.assertGreaterEqual(third["risk"]["score"], 70)
        self.assertEqual(third["risk"]["context"]["event_count"], 3)
        self.assertEqual(len(self.store.list_incidents()), 1)
        self.assertEqual(len(self.store.list_incidents()[0]["evidence_events"]), 3)

    def test_doorbell_before_person_reduces_expected_arrival_score(self):
        first = self.pipeline.ingest_ring(
            self.event("doorbell", "doorbell.pressed", 0, hour=12), True
        )
        second = self.pipeline.ingest_ring(
            self.event("visitor", "person.detected", 1, hour=12), True
        )
        self.assertEqual(first["incident_id"], second["incident_id"])
        self.assertEqual(second["risk"]["context"]["expected_sequence_adjustment"], -12)
        self.assertEqual(second["risk"]["score"], 7)

    def test_different_zone_or_late_event_starts_new_incident(self):
        first = self.pipeline.ingest_ring(self.event("first", "motion.detected", 0), True)
        other_zone = self.event("zone", "motion.detected", 1)
        other_zone["zone_id"] = "back_gate"
        second = self.pipeline.ingest_ring(other_zone, True)
        third = self.pipeline.ingest_ring(self.event("late", "motion.detected", 10), True)
        self.assertNotEqual(first["incident_id"], second["incident_id"])
        self.assertNotEqual(first["incident_id"], third["incident_id"])

    def test_evolving_demo_exposes_score_progression(self):
        result = run_situation_demo(self.pipeline, "evolving_intrusion")
        scores = [stage["score"] for stage in result["stages"]]
        self.assertEqual(scores, sorted(scores))
        self.assertEqual(len(set(scores)), 3)
        self.assertGreaterEqual(scores[-1], 70)
        self.assertEqual(len(self.store.list_incidents()), 1)


if __name__ == "__main__":
    unittest.main()
