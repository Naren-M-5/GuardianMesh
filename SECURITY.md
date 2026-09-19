# Security policy

Do not report vulnerabilities in a public issue. Until a private disclosure address is configured, contact the repository owner directly.

Never commit real webhook secrets, Ring credentials, private video, household routines, addresses, or production event exports. Rotate a secret immediately if it appears in git history.

Supported security properties in V1:

- HMAC-SHA256 webhook verification with constant-time comparison
- replay-window validation and source-event idempotency
- parameterized SQLite statements
- deterministic action allow/confirm/deny policy
- no unrestricted SQL, shell, or arbitrary HTTP tools for the agent
- raw media excluded from canonical storage by default
