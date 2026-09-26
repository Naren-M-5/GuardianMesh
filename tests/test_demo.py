import unittest
from packages.guardianmesh_core.demo import run_demo
from packages.guardianmesh_core.storage import Store


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def tearDown(self):
        self.store.connection.close()

    def test_scenario_scores_and_labels(self):
        for scenario, score in [
            ("intrusion", 78), ("late_resident", 46), ("delivery", 19), ("routine", 0)
        ]:
            result = run_demo(self.store, scenario)
            self.assertEqual(result["risk"]["score"], score)
            self.assertTrue(self.store.get_incident(result["incident_id"])["title"].startswith("Simulation:"))
        for event in self.store.list_events():
            self.assertEqual(event["source"], "simulation")
            self.assertTrue(event["integrity"]["simulation_declared"])
            self.assertFalse(event["integrity"]["signature_verified"])

    def test_repeat_runs_and_audit(self):
        a = run_demo(self.store, "intrusion")
        b = run_demo(self.store, "intrusion")
        self.assertNotEqual(a["incident_id"], b["incident_id"])
        self.store.transition_incident(a["incident_id"], "acknowledged", "local_home_owner")
        self.store.transition_incident(a["incident_id"], "resolved", "local_home_owner", "Demo reviewed")
        self.assertEqual(len(self.store.list_incident_audit(a["incident_id"])), 2)
        self.assertEqual(len(self.store.list_events()), 2)

    def test_late_resident_feedback_lowers_repeat_but_intrusion_stays_high(self):
        first_score = None
        for index in range(3):
            result = run_demo(self.store, "late_resident")
            first_score = first_score or result["risk"]["score"]
            self.store.transition_incident(
                result["incident_id"], "resolved", "local_home_owner",
                f"Confirmed resident arrival {index}", "resident",
            )
        learned = run_demo(self.store, "late_resident")
        intrusion = run_demo(self.store, "intrusion")
        self.assertEqual(first_score, 46)
        self.assertEqual(learned["risk"]["score"], 7)
        self.assertEqual(learned["risk"]["context"]["assessment_mode"], "adaptive")
        self.assertGreaterEqual(intrusion["risk"]["score"], 70)
        self.assertIn(
            "BASELINE_ZONE_DEVIATION",
            {factor["code"] for factor in intrusion["risk"]["evidence"]},
        )

    def test_unknown_scenario_writes_nothing(self):
        with self.assertRaises(ValueError):
            run_demo(self.store, "../unknown")
        self.assertEqual(self.store.list_events(), [])
