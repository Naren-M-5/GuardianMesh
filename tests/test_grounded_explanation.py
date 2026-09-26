import json
import unittest

from packages.guardianmesh_core.demo import run_situation_demo
from packages.guardianmesh_core.explanation import explain_incident
from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import Store


class GroundedExplanationTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.pipeline = GuardianPipeline(self.store)

    def tearDown(self):
        self.store.connection.close()

    def explanation_for(self, scenario):
        result = run_situation_demo(self.pipeline, scenario)
        incident = self.store.get_incident(result["incident_id"])
        events = [event.to_dict() for event in self.store.get_events_by_ids(incident["evidence_events"])]
        return explain_incident(incident, events)

    def test_intrusion_explanation_is_grounded_and_reconstructs_score(self):
        explanation = self.explanation_for("evolving_intrusion")
        calculation = explanation["calculation"]
        self.assertEqual(
            calculation["final_score"],
            calculation["evidence_total"] + sum(calculation["adjustments"].values()),
        )
        self.assertEqual(explanation["situation"]["event_count"], 3)
        self.assertIn("3 related signals", explanation["narrative"])
        self.assertTrue(explanation["counterfactuals"])
        serialized = json.dumps(explanation)
        self.assertNotIn("device_id", serialized)
        self.assertNotIn("source_event_id", serialized)

    def test_expected_delivery_explains_context_reduction(self):
        explanation = self.explanation_for("expected_delivery")
        self.assertEqual(explanation["calculation"]["adjustments"]["expected_sequence"], -12)
        self.assertIn("reduced the result by 12 points", explanation["narrative"])
        self.assertEqual(
            explanation["situation"]["sequence"],
            ["doorbell.pressed", "person.detected", "motion.detected"],
        )

    def test_counterfactuals_are_deterministic(self):
        explanation = self.explanation_for("evolving_intrusion")
        for item in explanation["counterfactuals"]:
            self.assertEqual(item["score"], max(0, explanation["score"] + item["change"]))


if __name__ == "__main__":
    unittest.main()
