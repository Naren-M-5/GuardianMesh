import unittest

from packages.guardianmesh_core.normalizer import normalize_ring
from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import Store


class EventProvenanceTests(unittest.TestCase):
    def test_signed_webhook_does_not_imply_real_device(self):
        event = normalize_ring({"id": "signed", "type": "motion.detected"}, True)
        self.assertEqual(event.integrity["ingestion_method"], "webhook")
        self.assertFalse(event.integrity["simulation_declared"])

    def test_simulation_declaration_is_persisted_and_deduplicated(self):
        store = Store(":memory:")
        try:
            pipeline = GuardianPipeline(store)
            payload = {"id": "simulation", "type": "motion.detected", "simulation": True}
            pipeline.ingest_ring(payload, True)
            self.assertTrue(pipeline.ingest_ring(payload, True)["duplicate"])
            events = store.list_events()
            self.assertEqual(len(events), 1)
            self.assertTrue(events[0]["integrity"]["simulation_declared"])
        finally:
            store.connection.close()

    def test_sender_cannot_claim_history_ingestion(self):
        event = normalize_ring({
            "id": "spoof", "type": "motion.detected", "simulation": "false",
            "integrity": {"ingestion_method": "ring_history", "authenticated_source": True},
        }, False)
        self.assertEqual(event.integrity["ingestion_method"], "webhook")
        self.assertNotIn("authenticated_source", event.integrity)
        self.assertFalse(event.integrity["simulation_declared"])
