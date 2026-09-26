import unittest

from packages.guardianmesh_core.evaluation import run_evaluation


class EvaluationTests(unittest.TestCase):
    def test_labeled_scenarios_pass_without_false_alerts_or_misses(self) -> None:
        report = run_evaluation()
        metrics = report["metrics"]
        self.assertEqual((metrics["passed"], metrics["total"]), (7, 7))
        self.assertEqual(metrics["false_positives"], 0)
        self.assertEqual(metrics["false_negatives"], 0)

    def test_feedback_reduces_late_resident_risk(self) -> None:
        learning = run_evaluation()["learning"]
        self.assertEqual(learning["late_resident_cold_score"], 46)
        self.assertEqual(learning["late_resident_learned_score"], 7)
        self.assertEqual(learning["risk_reduction"], 39)

    def test_report_is_explicitly_synthetic_and_deterministic(self) -> None:
        first = run_evaluation()
        second = run_evaluation()
        self.assertTrue(first["synthetic"])
        self.assertIn("not measure performance in real households", first["limitations"])
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
