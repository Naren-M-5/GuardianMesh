# API contract

Base path: `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness/version |
| POST | `/integrations/ring/webhook` | Signed Ring event ingestion |
| GET | `/integrations/ring/devices` | Local Ring device discovery |
| POST | `/integrations/ring/sync` | Import and deduplicate Ring event history |
| GET | `/integrations/ring/sync/status` | Last Ring synchronization result |
| GET | `/events` | Canonical event list |
| GET | `/incidents` | Incident list |
| GET | `/incidents/{id}` | Incident detail |
| GET | `/incidents/{id}/explanation` | Numeric evidence explanation |
| POST | `/incidents/{id}/acknowledge` | Record owner acknowledgement |
| POST | `/incidents/{id}/resolve` | Resolve with a required note |
| GET | `/incidents/{id}/audit` | Incident action audit history |
| GET | `/policy/{action}` | Inspect deterministic action decision |

Planned: SSE stream, routine profiles, privacy preferences, daily summary, and evidence-grounded Guardian queries.

The webhook returns `202` and does not run an LLM. Production processing will publish asynchronously after persistence.
