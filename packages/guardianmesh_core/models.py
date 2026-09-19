from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:20]}"


@dataclass(slots=True)
class CanonicalEvent:
    source: str
    source_event_id: str
    event_type: str
    occurred_at: str
    space_id: str
    device_id: str
    zone_id: str
    event_id: str = field(default_factory=lambda: new_id("evt"))
    schema_version: str = "1.0"
    received_at: str = field(default_factory=utc_now)
    classification: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)
    media: dict[str, Any] = field(default_factory=lambda: {
        "available": False, "retention": "ephemeral", "reference": None
    })
    integrity: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskFactor:
    code: str
    weight: int
    value: float
    explanation: str


@dataclass(slots=True)
class RiskAssessment:
    incident_id: str
    score: int
    level: str
    evidence: list[RiskFactor]
    model_confidence: float
    risk_assessment_id: str = field(default_factory=lambda: new_id("risk"))
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
