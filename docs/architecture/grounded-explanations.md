# Evidence-grounded explanations

The Guardian explanation layer converts stored risk evidence into a readable
account of an incident. It does not call a language model, infer missing facts,
or modify the assessment.

For each incident it returns:

- a narrative derived from event count, level, score, and strongest factors
- the complete evidence contribution total
- familiarity and expected-sequence adjustments
- the final deterministic score
- ordered situation event types
- counterfactual scores with one factor removed
- explicit grounding and limitation statements

Device IDs, source event IDs, media references, and raw payloads are excluded.
The counterfactuals explain sensitivity; they are not predictions of what would
have happened in the physical world.

The separation between assessment and explanation is a safety boundary:
algorithms determine risk, while the explanation layer can only describe the
persisted result.
