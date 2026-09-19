# Threat model

| Threat | Control | Residual risk |
|---|---|---|
| Forged webhook | HMAC verification, constant-time compare | Secret compromise |
| Replay | Five-minute timestamp window, idempotency key | Valid replay inside window is deduplicated |
| Duplicate delivery | Unique provider event key | Incorrect provider IDs |
| Agent invents evidence | Structured read-only tools and evidence IDs | Misleading phrasing; UI exposes source facts |
| Agent triggers unsafe action | Deterministic policy gate | Policy implementation bugs |
| Sensitive media leak | Ephemeral default, no raw media in event schema | External provider retention |
| Routine-profile exposure | Least privilege, encryption in AWS | Authorized-account compromise |
| SQL injection | Parameterized queries | Unsafe future query code |

Out of scope for V1: facial identification, medical diagnosis, automatic police calls, and covert continuous audio storage.
