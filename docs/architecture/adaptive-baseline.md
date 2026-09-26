# Adaptive household baseline

GuardianMesh learns only from events that a homeowner has resolved with one of
four benign outcomes: resident, expected visitor, delivery, or harmless activity.
Unresolved incidents, suspicious outcomes, unknown outcomes, and camera live-view
sessions never become examples of normal household behavior.

The baseline stores metadata summaries rather than identity or media:

- confirmed active hours
- common event types and zones
- median activity duration
- coarse three-hour event patterns
- sample count and confidence

Three confirmed samples move a space from `learning` to `ready`. This deliberately
small threshold makes the hackathon behavior demonstrable; a production deployment
would require a longer calibration period and evaluation with real households.

## Assessment behavior

During cold start, the deterministic quiet-hour rule remains active. In adaptive
mode, time is compared with confirmed active hours. A pattern seen at least twice
receives a visible `-12` familiarity adjustment. This adjustment cannot erase the
underlying evidence: person presence remains visible, and a new zone, prolonged
activity, or a rare sequence adds independent risk factors.

The risk response includes a `context` object recording assessment mode, sample
count, baseline confidence, known-pattern count, and the applied adjustment. This
makes before-and-after behavior auditable.

## Safety boundary

The baseline does not identify residents, infer medical conditions, or authorize
physical or emergency actions. A homeowner classification is feedback about an
event pattern, not proof of a person's identity.
