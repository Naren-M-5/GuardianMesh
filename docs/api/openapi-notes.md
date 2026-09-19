# API contract

Base path: `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness/version |
| POST | `/integrations/ring/webhook` | Signed Ring event ingestion |
| GET | `/events` | Canonical event list |
| GET | `/incidents` | Incident list |
| GET | `/incidents/{id}` | Incident detail |
| GET | `/incidents/{id}/explanation` | Numeric evidence explanation |
| GET | `/policy/{action}` | Inspect deterministic action decision |

Planned: incident resolution, SSE stream, routine profiles, privacy preferences, daily summary, and evidence-grounded Guardian queries.

The webhook returns `202` and does not run an LLM. Production processing will publish asynchronously after persistence.
