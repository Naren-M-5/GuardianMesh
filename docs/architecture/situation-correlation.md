# Situation correlation

Ring signals are useful individually but become more informative as a sequence.
GuardianMesh correlates activity from the same space and zone when consecutive
events occur within five minutes. The incident keeps one stable ID while its
evidence list, score, severity, and explanation evolve.

## Examples

An unusual motion signal followed by a person and prolonged rare activity grows
from an observation into a high-risk incident. Three or more related activity
signals add `REPEATED_ACTIVITY` evidence.

A doorbell press followed by a person is recognized as an expected arrival
sequence and receives a visible `-12` contextual adjustment. The person evidence
is retained; the adjustment changes interpretation rather than deleting evidence.

Signals from another zone or more than five minutes later start a new incident.
Live-view sessions stay in history and are not correlated into activity threats.

## Auditability

The risk `context` records event count, ordered event types, correlation window,
baseline state, familiarity adjustment, and expected-sequence adjustment. The
dashboard shows the ordered sequence alongside the incident evidence.

Correlation is deterministic and metadata-only. It does not identify people,
inspect raw video, or authorize physical actions.
