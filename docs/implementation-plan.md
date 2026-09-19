# Five-week implementation plan

## Week 1 — Heartbeat

- Register Ring developer access and run the official simulator
- Map the real webhook envelope into `normalize_ring`
- Verify official signature headers and retry behavior
- Display accepted canonical events
- Log onboarding friction immediately

Exit: an authentic Ring simulator event reaches the local API and is visible through `/events`.

## Week 2 — Temporal intelligence

- Window correlated events into observations
- Learn hourly/weekday/zone baselines
- Add cyclical time, duration, zone-rarity, and sequence-frequency features
- Build normal-day, delivery, unusual-visitor, intrusion, and late-resident fixtures

Exit: reproducible anomaly metrics and false-positive evaluation.

## Week 3 — Incidents and Guardian

- Stabilize risk weights and evidence codes
- Add incident lifecycle and user resolution feedback
- Implement read-only Guardian tools and grounded answers
- Integrate Strands/Bedrock with citations to incident/evidence IDs

Exit: “Why did you alert me?” answers only from stored evidence.

## Week 4 — AWS and privacy

- Deploy ingestion/API with API Gateway, Lambda, EventBridge, DynamoDB
- Deploy agent to AgentCore Runtime
- Add least-privilege IAM, budgets, audit logging, lifecycle retention
- Complete threat model and privacy controls

Exit: official Ring event and AWS services execute in the hosted demo.

## Week 5 — Judge-ready product

- Build incident timeline, explanation panel, Privacy Shield, daily intelligence
- Rehearse intrusion and late-resident self-correction scenarios
- Finish tests, model card, architecture diagram, setup docs, friction log
- Record an English demo under three minutes and prepare Devpost answers

Exit: clean-room setup succeeds and every submission claim is demonstrable.
