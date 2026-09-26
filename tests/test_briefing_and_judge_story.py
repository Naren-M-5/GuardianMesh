import unittest

from packages.guardianmesh_core.briefing import build_household_briefing
from packages.guardianmesh_core.demo import run_demo, run_judge_story
from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import Store


class BriefingAndJudgeStoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(":memory:")

    def tearDown(self) -> None:
        self.store.connection.close()

    def test_quiet_briefing_does_not_claim_home_is_safe(self) -> None:
        report = build_household_briefing([], [])
        self.assertEqual(report["state"], "quiet")
        self.assertIn("No unresolved high-risk", report["headline"])
        self.assertIn("does not confirm safety", report["limitations"])

    def test_intrusion_briefing_requests_human_review(self) -> None:
        run_demo(self.store, "intrusion")
        report = build_household_briefing(
            self.store.list_incidents(), self.store.list_events()
        )
        self.assertEqual(report["state"], "attention")
        self.assertEqual(report["counts"]["attention_situations"], 1)
        self.assertEqual(report["notable"][0]["score"], 78)
        self.assertNotIn("incident_id", report["notable"][0])

    def test_judge_story_correlates_and_explains_three_signals(self) -> None:
        story = run_judge_story(GuardianPipeline(self.store), self.store)
        self.assertTrue(story["simulation"])
        self.assertEqual([stage["score"] for stage in story["stages"]], [27, 46, 89])
        self.assertEqual(story["explanation"]["situation"]["event_count"], 3)
        self.assertEqual(story["explanation"]["score"], 89)
        self.assertIn("no identity recognition", story["privacy"])


if __name__ == "__main__":
    unittest.main()
