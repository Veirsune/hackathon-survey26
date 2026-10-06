# Benchmark

A frozen 12-night synthetic world built from public A inputs and delivered D1 notes, with real Kimi calls:

| Strategy | Score | Required missing | Calls / JSON replies | Model seconds |
|---|---:|---:|---|---:|
| Parent claim reconciliation | -14069.735930 | 385 | 2 / 1 | 51.639 |
| Direction-isolated validation | -12792.643315 | 364 | 1 / 1 | 23.941 |

Both completed without planner errors. The +1277.092615 difference is not an isolated algorithm effect: the candidate obtained the same applicable terrain limits one night earlier. No partial acceptance survives in the retained log tail. These are synthetic scores, not formal-card results.

Ten mechanism checks cover an actual rejected B1 reply, strict quote validation, whole-direction quarantine, and retention of pending evidence. Bad or ambiguous direction metadata still rejects the whole response. Formal eight-card validation is pending.
