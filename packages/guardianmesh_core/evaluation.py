"""Reproducible synthetic benchmark for GuardianMesh decision behavior."""
from __future__ import annotations

from typing import Any

from .demo import run_demo, run_situation_demo
from .pipeline import GuardianPipeline
from .storage import Store

ALERT_THRESHOLD = 40


def _single_demo(scenario: str) -> int:
    store = Store(":memory:")
    try:
        return int(run_demo(store, scenario)["risk"]["score"])
    finally:
        store.connection.close()


def _situation_demo(scenario: str) -> int:
    store = Store(":memory:")
    try:
        return int(run_situation_demo(GuardianPipeline(store), scenario)["risk"]["score"])
    finally:
        store.connection.close()


def _learned_late_resident() -> tuple[int, int]:
    store = Store(":memory:")
    try:
        cold_score = 0
        for index in range(3):
            result = run_demo(store, "late_resident")
            cold_score = cold_score or int(result["risk"]["score"])
            store.transition_incident(
                result["incident_id"], "resolved", "evaluation",
                f"Confirmed resident pattern {index}", "resident",
            )
        learned_score = int(run_demo(store, "late_resident")["risk"]["score"])
        return cold_score, learned_score
    finally:
        store.connection.close()


def _live_view_score() -> int:
    store = Store(":memory:")
    try:
        result = GuardianPipeline(store).ingest_ring({
            "id": "evaluation-live-view", "type": "live_view.started",
            "occurred_at": "2026-09-20T02:00:00Z", "space_id": "evaluation",
            "device_id": "camera", "zone_id": "entrance",
            "attributes": {"duration_seconds": 600}, "simulation": True,
        }, False)
        return int(result["risk"]["score"])
    finally:
        store.connection.close()


def run_evaluation() -> dict[str, Any]:
    cold_late, learned_late = _learned_late_resident()
    definitions = [
        ("routine", False, _single_demo("routine")),
        ("delivery", False, _single_demo("delivery")),
        ("expected_delivery_sequence", False, _situation_demo("expected_delivery")),
        ("learned_late_resident", False, learned_late),
        ("homeowner_live_view", False, _live_view_score()),
        ("intrusion", True, _single_demo("intrusion")),
        ("evolving_intrusion", True, _situation_demo("evolving_intrusion")),
    ]
    cases = [
        {
            "scenario": name, "expected_attention": expected,
            "score": score, "predicted_attention": score >= ALERT_THRESHOLD,
            "passed": expected == (score >= ALERT_THRESHOLD),
        }
        for name, expected, score in definitions
    ]
    tp = sum(case["expected_attention"] and case["predicted_attention"] for case in cases)
    tn = sum(not case["expected_attention"] and not case["predicted_attention"] for case in cases)
    fp = sum(not case["expected_attention"] and case["predicted_attention"] for case in cases)
    fn = sum(case["expected_attention"] and not case["predicted_attention"] for case in cases)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return {
        "benchmark": "guardianmesh_synthetic_safety_v1",
        "synthetic": True,
        "alert_threshold": ALERT_THRESHOLD,
        "cases": cases,
        "metrics": {
            "total": len(cases), "passed": tp + tn,
            "true_positives": tp, "true_negatives": tn,
            "false_positives": fp, "false_negatives": fn,
            "precision": round(precision, 3), "recall": round(recall, 3),
        },
        "learning": {
            "late_resident_cold_score": cold_late,
            "late_resident_learned_score": learned_late,
            "risk_reduction": cold_late - learned_late,
        },
        "limitations": (
            "Deterministic synthetic scenarios validate logic and regressions; "
            "they do not measure performance in real households."
        ),
    }
