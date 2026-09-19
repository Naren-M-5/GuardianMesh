# GuardianMesh

Privacy-first situational intelligence for Ring events. GuardianMesh learns normal activity, detects temporal anomalies, produces explainable risk assessments, and keeps consequential actions behind deterministic policy and human control.

> Models perceive. Algorithms assess. Policies authorize. Agents explain and coordinate. Humans retain control over consequential actions.

## V1 scope

`Ring/Simulator -> signed webhook -> canonical event -> SQLite -> temporal features -> risk assessment -> incident -> API/dashboard`

Companion Mode and conflict de-escalation are intentionally deferred until the core safety pipeline works end to end.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn apps.api.app.main:app --reload
```

In another terminal:

```bash
python scripts/replay_scenario.py simulations/intrusion/events.json
```

Open `http://127.0.0.1:8000/docs`, or run:

```bash
curl http://127.0.0.1:8000/api/v1/events
curl http://127.0.0.1:8000/api/v1/incidents
```

## Test

Core tests need only Python's standard library:

```bash
python -m unittest discover -s tests -v
```

API tests are enabled after installing the dev dependencies.

## Repository map

- `apps/api`: FastAPI boundary and composition root
- `packages/guardianmesh_core`: canonical schemas, storage, temporal/risk/policy logic
- `apps/dashboard`: dashboard contract and starter UI notes
- `services`: deployment boundaries for later extraction
- `simulations`: deterministic demo scenarios
- `docs`: architecture, API, privacy, threat model, and ADRs
- `infrastructure/aws`: AWS deployment design

## Safety boundaries

- The agent cannot set or modify risk scores.
- Unknown people are never identified.
- Raw media is ephemeral by default.
- Autonomous emergency calls and claims of police contact are denied.
- Every risk contribution and action decision is auditable.

## Hackathon targets

- Primary: Ring
- Mini challenges: AWS Builder and Open Source

The final submission must demonstrate Ring technology executing at runtime via the official simulator or a device. The local simulator included here is for development and automated tests, not a substitute for the official Ring demonstration.

## License

Apache-2.0. Keep the remote repository private until the owner explicitly decides to publish or share it.
