# Logical services

These folders are architectural boundaries inside the V1 modular monolith. Extract them only when deployment or scaling needs justify it.

- `ring-ingestion`: verification, validation, normalization, deduplication
- `temporal-engine`: windows, routines, sequences, cyclical features
- `anomaly-engine`: unusualness scoring and model evaluation
- `situation-engine`: risk, evidence, incident lifecycle
- `guardian-agent`: evidence-grounded explanation tools
- `action-engine`: policy checks, execution, audit
