import unittest

from packages.guardianmesh_core.normalizer import normalize_ring_history
from packages.guardianmesh_core.pipeline import GuardianPipeline
from packages.guardianmesh_core.storage import Store


class RingSyncTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.pipeline = GuardianPipeline(self.store)
        self.record = {
            "type": "history-events",
            "id": "directed_event_001",
            "attributes": {
                "event_type": "motion.human",
                "is_third_party_reviewed": False,
                "start": 1699457200000,
                "end": 1699457225000,
            },
            "relationships": {
                "source": {"data": {"type": "devices", "id": "directed_device_001"}}
            },
        }

    def test_history_event_is_normalized(self):
        event = normalize_ring_history(self.record)
        self.assertEqual(event.source_event_id, "directed_event_001")
        self.assertEqual(event.event_type, "person.detected")
        self.assertEqual(event.occurred_at, "2023-11-08T15:26:40Z")
        self.assertEqual(event.attributes["duration_seconds"], 25.0)
        self.assertTrue(event.integrity["authenticated_source"])

    def test_history_import_is_idempotent(self):
        first = self.pipeline.ingest_ring_history(self.record)
        second = self.pipeline.ingest_ring_history(self.record)
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(len(self.store.list_events()), 1)
        self.assertEqual(len(self.store.list_incidents()), 1)

    def test_sync_state_round_trip(self):
        state = {"status": "ok", "last_synced_at": "2026-09-19T12:00:00Z", "imported": 3}
        self.store.set_integration_state("ring", state)
        self.assertEqual(self.store.get_integration_state("ring"), state)

    def test_rejects_unknown_history_event(self):
        self.record["attributes"]["event_type"] = "unknown"
        with self.assertRaises(ValueError):
            normalize_ring_history(self.record)


if __name__ == "__main__":
    unittest.main()
