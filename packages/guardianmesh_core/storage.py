from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import CanonicalEvent, RiskAssessment, utc_now


class InvalidIncidentTransition(ValueError):
    """Raised when an incident status change is not allowed."""


class Store:
    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.migrate()

    def migrate(self) -> None:
        self.connection.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS events (
          event_id TEXT PRIMARY KEY, source TEXT NOT NULL, source_event_id TEXT NOT NULL,
          space_id TEXT NOT NULL, device_id TEXT NOT NULL, zone_id TEXT NOT NULL,
          event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, received_at TEXT NOT NULL,
          payload_json TEXT NOT NULL, UNIQUE(source, source_event_id)
        );
        CREATE INDEX IF NOT EXISTS idx_events_space_time ON events(space_id, occurred_at);
        CREATE TABLE IF NOT EXISTS incidents (
          incident_id TEXT PRIMARY KEY, space_id TEXT NOT NULL, type TEXT NOT NULL,
          status TEXT NOT NULL, severity TEXT NOT NULL, title TEXT NOT NULL,
          started_at TEXT NOT NULL, updated_at TEXT NOT NULL, risk_json TEXT NOT NULL,
          evidence_json TEXT NOT NULL, resolution TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_incidents_space_time ON incidents(space_id, started_at);
        CREATE TABLE IF NOT EXISTS audit_logs (
          audit_id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL,
          actor TEXT NOT NULL, action TEXT NOT NULL, object_id TEXT, details_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS integration_state (
          integration TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        """)
        self.connection.commit()

    def add_event(self, event: CanonicalEvent) -> tuple[CanonicalEvent, bool]:
        try:
            self.connection.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event.event_id, event.source, event.source_event_id, event.space_id,
                 event.device_id, event.zone_id, event.event_type, event.occurred_at,
                 event.received_at, json.dumps(event.to_dict())),
            )
            self.connection.commit()
            return event, True
        except sqlite3.IntegrityError:
            row = self.connection.execute(
                "SELECT payload_json FROM events WHERE source=? AND source_event_id=?",
                (event.source, event.source_event_id),
            ).fetchone()
            data = json.loads(row["payload_json"])
            data["integrity"]["duplicate"] = True
            return CanonicalEvent(**data), False

    def list_events(self, space_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if space_id:
            rows = self.connection.execute(
                "SELECT payload_json FROM events WHERE space_id=? ORDER BY occurred_at DESC LIMIT ?",
                (space_id, limit),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT payload_json FROM events ORDER BY occurred_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def add_incident(self, incident: dict[str, Any], risk: RiskAssessment) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO incidents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (incident["incident_id"], incident["space_id"], incident["type"], incident["status"],
             incident["severity"], incident["title"], incident["started_at"],
             incident["updated_at"], json.dumps(risk.to_dict()),
             json.dumps(incident["evidence_events"]), incident.get("resolution")),
        )
        self.connection.commit()

    def list_incidents(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM incidents ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._incident(row) for row in rows]

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM incidents WHERE incident_id=?", (incident_id,)
        ).fetchone()
        return self._incident(row) if row else None

    def transition_incident(
        self,
        incident_id: str,
        target_status: str,
        actor: str,
        resolution: str | None = None,
    ) -> dict[str, Any] | None:
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        current_status = str(incident["status"])
        allowed = {
            "active": {"acknowledged", "resolved"},
            "observed": {"acknowledged", "resolved"},
            "acknowledged": {"resolved"},
            "resolved": set(),
        }
        if target_status not in allowed.get(current_status, set()):
            raise InvalidIncidentTransition(
                f"Incident cannot change from {current_status} to {target_status}."
            )

        clean_resolution = resolution.strip() if resolution else None
        if target_status == "resolved" and not clean_resolution:
            raise InvalidIncidentTransition("A resolution note is required.")

        occurred_at = utc_now()
        details = {
            "from_status": current_status,
            "to_status": target_status,
            "resolution": clean_resolution,
        }
        with self.connection:
            self.connection.execute(
                "UPDATE incidents SET status=?, updated_at=?, resolution=? WHERE incident_id=?",
                (target_status, occurred_at, clean_resolution, incident_id),
            )
            self.connection.execute(
                "INSERT INTO audit_logs (occurred_at, actor, action, object_id, details_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    occurred_at,
                    actor,
                    f"incident.{target_status}",
                    incident_id,
                    json.dumps(details),
                ),
            )
        return self.get_incident(incident_id)

    def list_incident_audit(self, incident_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT audit_id, occurred_at, actor, action, object_id, details_json "
            "FROM audit_logs WHERE object_id=? ORDER BY audit_id DESC LIMIT ?",
            (incident_id, limit),
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["details"] = json.loads(item.pop("details_json"))
            items.append(item)
        return items

    def set_integration_state(self, integration: str, state: dict[str, Any]) -> None:
        updated_at = str(state.get("updated_at") or state.get("last_synced_at") or "")
        self.connection.execute(
            "INSERT OR REPLACE INTO integration_state VALUES (?, ?, ?)",
            (integration, json.dumps(state), updated_at),
        )
        self.connection.commit()

    def get_integration_state(self, integration: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT state_json FROM integration_state WHERE integration=?", (integration,)
        ).fetchone()
        return json.loads(row["state_json"]) if row else None

    @staticmethod
    def _incident(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["risk"] = json.loads(data.pop("risk_json"))
        data["evidence_events"] = json.loads(data.pop("evidence_json"))
        return data
