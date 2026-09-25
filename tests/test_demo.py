import unittest
from packages.guardianmesh_core.demo import run_demo
from packages.guardianmesh_core.storage import Store


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def tearDown(self):
        self.store.connection.close()

    def test_scenario_scores_and_labels(self):
        for scenario, score in [("intrusion", 78), ("delivery", 19), ("routine", 0)]:
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

    def test_unknown_scenario_writes_nothing(self):
        with self.assertRaises(ValueError):
            run_demo(self.store, "../unknown")
        self.assertEqual(self.store.list_events(), [])
