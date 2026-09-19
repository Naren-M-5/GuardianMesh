# Data flow

`Ring payload -> signature verification -> CanonicalEvent -> temporal features -> anomaly -> risk evidence -> incident -> policy decision -> action/audit`

Raw provider payloads terminate at the ingestion boundary. Downstream components consume versioned canonical events. Media references are ephemeral and raw frames are discarded where possible.

Idempotency key: `(source, source_event_id)`.

Authoritative security history lives in SQLite locally and DynamoDB on AWS. Agent conversation memory is non-authoritative and must never replace event, incident, risk, action, or audit storage.
