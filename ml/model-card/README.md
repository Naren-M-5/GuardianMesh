# GuardianMesh decision system

GuardianMesh v0.1 uses deterministic evidence rules and a homeowner-confirmed behavioral baseline. It does not use face recognition, person identification, or a trained predictive model.

Intended use: flag unusual Ring event patterns for owner review. It is not intended for identity recognition, crime prediction, medical inference, or autonomous emergency response.

The reproducible synthetic benchmark is documented in `docs/evaluation.md` and runs with `python scripts/evaluate_scenarios.py`. Its results validate expected code behavior only; they are not real-world accuracy measurements.

Before production use, evaluation must include consenting-household field data, false alerts per normal day, alert latency, calibration, and subgroup or lighting-condition analysis where labels permit.
