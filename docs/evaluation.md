# Synthetic evaluation

GuardianMesh includes a deterministic benchmark that checks decision behavior without requiring a Ring token, physical camera, or network access.

Run it with:

```bash
python scripts/evaluate_scenarios.py
python scripts/evaluate_scenarios.py --json
```

## Benchmark contract

The alert threshold is 40. Seven labeled scenarios cover routine activity, delivery, an expected arrival sequence, a learned late-resident pattern, homeowner-initiated live view, intrusion, and an evolving multi-signal intrusion.

| Scenario | Expected | Score |
| --- | --- | ---: |
| Routine | No attention | 0 |
| Delivery | No attention | 19 |
| Expected delivery sequence | No attention | 18 |
| Learned late resident | No attention | 7 |
| Homeowner live view | No attention | 0 |
| Intrusion | Attention | 78 |
| Evolving intrusion | Attention | 89 |

The feedback test separately confirms that the same late-resident activity falls from 46 to 7 after three homeowner confirmations, while the intrusion scenarios remain above the alert threshold.

## What this proves

- Core rules remain reproducible across changes.
- Known benign situations stay below the alert threshold.
- Labeled threats remain above the threshold.
- Homeowner feedback changes future treatment of a matching routine.

## Limitations

This benchmark uses deterministic synthetic scenarios. A 7/7 result is a regression result, not a claim of real-world accuracy, safety certification, emergency detection, or performance across households. Field validation with consenting participants would be required before production use.
