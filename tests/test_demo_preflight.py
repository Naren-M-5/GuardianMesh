import tempfile
import unittest
from pathlib import Path

from scripts.demo_preflight import Probe, assess, token_is_configured


class DemoPreflightTests(unittest.TestCase):
    def test_token_check_never_requires_exposing_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("GUARDIANMESH_RING_ACCESS_TOKEN=secret-value\n", encoding="utf-8")
            self.assertTrue(token_is_configured(env_file))

    def test_recording_mode_passes_with_services_ring_and_evaluation(self) -> None:
        responses = {
            "/api/v1/health": Probe(True, 200, {"status": "healthy"}),
            "/api/v1/evaluation": Probe(True, 200, {"metrics": {"passed": 7, "total": 7}}),
            "/api/v1/integrations/ring/devices": Probe(True, 200, {"data": [{"id": "private"}]}),
            "/api/v1/integrations/ring/sync/status": Probe(
                True, 200, {"status": "ok", "last_synced_at": "2026-09-26T00:00:00Z"}
            ),
            "dashboard": Probe(True, 200, "html"),
        }
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("GUARDIANMESH_RING_ACCESS_TOKEN=configured\n", encoding="utf-8")
            def fake(url: str) -> Probe:
                if url.endswith(":3000"):
                    return responses["dashboard"]
                return responses[next(key for key in responses if key in url)]
            checks = assess("http://127.0.0.1:8000", "http://127.0.0.1:3000", env_file, True, fake)
        self.assertTrue(all(check.state == "pass" for check in checks))
        self.assertNotIn("secret", " ".join(check.detail for check in checks))

    def test_recording_mode_blocks_expired_token_and_offline_dashboard(self) -> None:
        def fake(url: str) -> Probe:
            if url.endswith(":3000"):
                return Probe(False, 0, error="offline")
            if url.endswith("/devices"):
                return Probe(False, 502, error="expired")
            if url.endswith("/evaluation"):
                return Probe(True, 200, {"metrics": {"passed": 7, "total": 7}})
            if url.endswith("/sync/status"):
                return Probe(True, 200, {"status": "never_synced"})
            return Probe(True, 200, {})
        with tempfile.TemporaryDirectory() as directory:
            checks = assess(
                "http://127.0.0.1:8000", "http://127.0.0.1:3000",
                Path(directory) / ".env", True, fake,
            )
        failures = {check.name for check in checks if check.state == "fail"}
        self.assertEqual(failures, {"Dashboard", "Ring token", "Ring device API"})


if __name__ == "__main__":
    unittest.main()
