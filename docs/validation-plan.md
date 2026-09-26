# Consent-based field validation plan

GuardianMesh currently reports deterministic synthetic benchmark results, not real-world accuracy. This protocol describes the next validation stage without claiming that it has already occurred.

## Pilot design

- Recruit 5–10 consenting households representing different schedules and household sizes.
- Run locally for 14 days per household.
- Store event metadata and homeowner labels only; do not collect video, audio, face embeddings, or identity labels.
- Let participants pause collection, inspect stored metadata, export their labels, and delete the local database.
- Obtain explicit consent from every participating household and exclude minors from labeling studies without guardian approval.

## Primary measures

- False alerts per normal household-day.
- Recall on participant-confirmed situations requiring attention.
- Median time from first signal to situation assessment.
- Risk-score change after confirmed benign feedback.
- Percentage of explanations participants rate as understandable.
- Percentage of recommended actions participants rate as appropriate.

## Safety review

GuardianMesh remains decision support. It must not identify people, diagnose health conditions, predict crime, or autonomously contact emergency services. Any future field result must include sample size, missing data, labeling procedure, and confidence intervals.
