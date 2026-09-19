import json
import time
import unittest

from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.policy import authorize
from packages.guardianmesh_core.signing import SignatureError, sign, verify
from packages.guardianmesh_core.storage import Store


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.pipeline = GuardianPipeline(self.store)
        self.event = {
            "id": "ring_test_001", "type": "person.detected",
            "occurred_at": "2026-09-19T02:13:08Z", "space_id": "space_test",
            "device_id": "ring_front", "zone_id": "entrance",
            "classification": {"label": "person", "confidence": 0.96},
            "attributes": {"duration_seconds": 74, "rare_sequence": True},
        }

    def test_intrusion_is_high_risk_and_explainable(self):
        result = self.pipeline.ingest_ring(self.event, True)
        self.assertGreaterEqual(result["risk"]["score"], 70)
        codes = {factor["code"] for factor in result["risk"]["evidence"]}
        self.assertEqual(codes, {"UNUSUAL_TIME", "PERSON_PRESENT", "PROLONGED_ACTIVITY", "RARE_SEQUENCE"})

    def test_duplicate_is_idempotent(self):
        first = self.pipeline.ingest_ring(self.event, True)
        second = self.pipeline.ingest_ring(self.event, True)
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(len(self.store.list_events()), 1)

    def test_signature_verification(self):
        body = json.dumps(self.event).encode()
        timestamp = str(int(time.time()))
        signature = sign(body, "secret", timestamp)
        verify(body, "secret", timestamp, f"sha256={signature}")
        with self.assertRaises(SignatureError):
            verify(body + b"x", "secret", timestamp, signature)

    def test_consequential_actions_are_bounded(self):
        self.assertEqual(authorize("send_dashboard_alert").decision, "allow")
        self.assertEqual(authorize("activate_deterrence").decision, "require_confirmation")
        self.assertEqual(authorize("autonomous_emergency_call").decision, "deny")
        self.assertEqual(authorize("made_up_action").decision, "deny")


if __name__ == "__main__":
    unittest.main()
