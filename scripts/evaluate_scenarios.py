"""Run the GuardianMesh synthetic safety benchmark."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.guardianmesh_core.evaluation import run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    report = run_evaluation()
    if args.json:
        print(json.dumps(report, indent=2))
        return
    metrics = report["metrics"]
    print(f"GuardianMesh synthetic benchmark: {metrics['passed']}/{metrics['total']} passed")
    for case in report["cases"]:
        status = "PASS" if case["passed"] else "FAIL"
        print(f"{status:4}  {case['scenario']:<28} score={case['score']:>3}")
    learning = report["learning"]
    print(
        "Late-resident feedback: "
        f"{learning['late_resident_cold_score']} -> {learning['late_resident_learned_score']} "
        f"({learning['risk_reduction']} point reduction)"
    )
    print(report["limitations"])


if __name__ == "__main__":
    main()
