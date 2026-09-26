"""Fail-fast readiness check for the GuardianMesh recording workflow."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Probe:
    ok: bool
    status: int
    body: Any = None
    error: str = ""


@dataclass(frozen=True)
class Check:
    name: str
    state: str
    detail: str
    recovery: str = ""


def fetch(url: str) -> Probe:
    try:
        request = Request(url, headers={"Accept": "application/json,text/html"})
        with urlopen(request, timeout=4) as response:  # noqa: S310 - localhost by CLI design
            raw = response.read().decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type", "")
            body: Any = raw
            if "json" in content_type:
                body = json.loads(raw)
            return Probe(True, response.status, body)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
            detail = str(body.get("detail") or body.get("error") or f"HTTP {exc.code}")
        except (json.JSONDecodeError, AttributeError):
            body, detail = raw, f"HTTP {exc.code}"
        return Probe(False, exc.code, body, detail)
    except (URLError, TimeoutError, OSError) as exc:
        return Probe(False, 0, error=str(exc.reason if isinstance(exc, URLError) else exc))


def token_is_configured(env_path: Path) -> bool:
    if os.getenv("GUARDIANMESH_RING_ACCESS_TOKEN", "").strip():
        return True
    if not env_path.exists():
        return False
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "GUARDIANMESH_RING_ACCESS_TOKEN":
            clean = value.strip().strip('"').strip("'")
            return bool(clean and clean.lower() not in {"change-me", "replace-me"})
    return False


def assess(
    api_base: str,
    dashboard_url: str,
    env_path: Path,
    recording: bool,
    probe: Callable[[str], Probe] = fetch,
) -> list[Check]:
    checks: list[Check] = []
    health = probe(f"{api_base}/api/v1/health")
    checks.append(Check(
        "FastAPI", "pass" if health.ok else "fail",
        "Local API is responding." if health.ok else "Local API is unavailable.",
        "Start Terminal 1 on port 8000." if not health.ok else "",
    ))

    dashboard = probe(dashboard_url)
    checks.append(Check(
        "Dashboard", "pass" if dashboard.ok else "fail",
        "Next.js dashboard is responding." if dashboard.ok else "Dashboard is unavailable.",
        "Start Terminal 2 with npm run dev." if not dashboard.ok else "",
    ))

    evaluation = probe(f"{api_base}/api/v1/evaluation")
    metrics = (
        evaluation.body.get("metrics", {})
        if evaluation.ok and isinstance(evaluation.body, dict) else {}
    )
    eval_ready = (
        evaluation.ok
        and metrics.get("passed") == metrics.get("total")
        and metrics.get("total", 0) > 0
    )
    checks.append(Check(
        "Synthetic benchmark", "pass" if eval_ready else "fail",
        f"{metrics.get('passed')}/{metrics.get('total')} labeled scenarios passed." if eval_ready
        else "Benchmark is unavailable or has a regression.",
        "Run python -m pytest -q and python scripts/evaluate_scenarios.py."
        if not eval_ready else "",
    ))

    configured = token_is_configured(env_path)
    token_state = "pass" if configured else ("fail" if recording else "warn")
    checks.append(Check(
        "Ring token", token_state,
        "A local token is configured; its value was not read into output." if configured
        else "No local Ring token is configured.",
        "Generate a fresh Playground token, save it in .env, then restart Terminal 1."
        if not configured else "",
    ))

    devices = probe(f"{api_base}/api/v1/integrations/ring/devices")
    device_data = (
        devices.body.get("data", [])
        if devices.ok and isinstance(devices.body, dict) else []
    )
    devices_ready = devices.ok and isinstance(device_data, list) and len(device_data) > 0
    device_state = "pass" if devices_ready else ("fail" if recording else "warn")
    checks.append(Check(
        "Ring device API", device_state,
        f"{len(device_data)} authorized Ring device(s) reachable." if devices_ready
        else "Ring device access is unavailable or the token has expired.",
        "Refresh the Playground token, restart FastAPI, and run preflight again."
        if not devices_ready else "",
    ))

    sync = probe(f"{api_base}/api/v1/integrations/ring/sync/status")
    sync_body = sync.body if sync.ok and isinstance(sync.body, dict) else {}
    synced = sync.ok and sync_body.get("status") == "ok" and bool(sync_body.get("last_synced_at"))
    checks.append(Check(
        "Ring event sync", "pass" if synced else "warn",
        f"Last successful sync: {sync_body.get('last_synced_at')}" if synced
        else "No successful Ring event sync is recorded for this session.",
        "Use Sync Ring events once before recording." if not synced else "",
    ))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="GuardianMesh demo readiness check")
    parser.add_argument("--recording", action="store_true", help="Require live Ring access")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--dashboard", default="http://127.0.0.1:3000")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    checks = assess(
        args.api.rstrip("/"), args.dashboard.rstrip("/"), Path(args.env_file), args.recording
    )
    print("GuardianMesh demo preflight")
    print("=" * 31)
    for check in checks:
        print(f"[{check.state.upper():4}] {check.name}: {check.detail}")
        if check.recovery:
            print(f"       Fix: {check.recovery}")
    failures = sum(check.state == "fail" for check in checks)
    warnings = sum(check.state == "warn" for check in checks)
    print("-" * 31)
    if failures:
        print(f"NOT READY — {failures} blocking check(s), {warnings} warning(s).")
        return 2
    print(f"READY{' FOR RECORDING' if args.recording else ''} — {warnings} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
