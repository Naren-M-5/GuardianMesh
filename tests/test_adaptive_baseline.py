import unittest

from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import Store


class AdaptiveBaselineTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.pipeline = GuardianPipeline(self.store)

    def tearDown(self):
        self.store.connection.close()

    def event(self, event_id: str, hour: int = 2, *, duration: int = 10,
              rare: bool = False) -> dict:
        return {
            "id": event_id,
            "type": "person.detected",
            "occurred_at": f"2026-09-20T{hour:02d}:10:00Z",
            "space_id": "care_home",
            "device_id": "front_camera",
            "zone_id": "front_entrance",
            "classification": {"label": "person", "confidence": 0.96},
            "attributes": {"duration_seconds": duration, "rare_sequence": rare},
        }

    def confirm_benign(self, event_id: str) -> dict:
        result = self.pipeline.ingest_ring(self.event(event_id), True)
        self.store.transition_incident(
            result["incident_id"], "resolved", "test_homeowner",
            resolution="Confirmed resident arrival", resolution_outcome="resident",
        )
        return result

    def test_confirmed_feedback_builds_ready_privacy_preserving_baseline(self):
        for index in range(3):
            self.confirm_benign(f"arrival-{index}")

        baseline = self.store.get_baseline("care_home")
        self.assertEqual(baseline["status"], "ready")
        self.assertEqual(baseline["sample_count"], 3)
        self.assertEqual(baseline["active_hours"], [2])
        self.assertEqual(baseline["usual_zones"], ["front_entrance"])
        self.assertNotIn("device_id", baseline)

    def test_known_pattern_reduces_repeat_alert_without_hiding_evidence(self):
        cold = self.confirm_benign("arrival-cold")
        self.confirm_benign("arrival-2")
        self.confirm_benign("arrival-3")

        learned = self.pipeline.ingest_ring(self.event("arrival-learned"), True)
        self.assertGreater(cold["risk"]["score"], learned["risk"]["score"])
        self.assertEqual(learned["risk"]["context"]["assessment_mode"], "adaptive")
        self.assertEqual(learned["risk"]["context"]["familiarity_adjustment"], -12)
        self.assertIn("PERSON_PRESENT", {item["code"] for item in learned["risk"]["evidence"]})

    def test_deviation_from_learned_routine_remains_high_risk(self):
        for index in range(3):
            self.confirm_benign(f"arrival-{index}")

        result = self.pipeline.ingest_ring(
            self.event("unusual", hour=14, duration=74, rare=True), True
        )
        codes = {item["code"] for item in result["risk"]["evidence"]}
        self.assertGreaterEqual(result["risk"]["score"], 70)
        self.assertIn("BASELINE_TIME_DEVIATION", codes)
        self.assertEqual(result["risk"]["context"]["assessment_mode"], "adaptive")

    def test_suspicious_outcome_does_not_train_normal_baseline(self):
        result = self.pipeline.ingest_ring(self.event("intruder"), True)
        self.store.transition_incident(
            result["incident_id"], "resolved", "test_homeowner",
            resolution="Confirmed suspicious activity",
            resolution_outcome="suspicious_activity",
        )
        self.assertEqual(self.store.get_baseline("care_home")["sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
