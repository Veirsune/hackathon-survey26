# Benchmark

A frozen 12-night synthetic world built from public A inputs and delivered D1 notes, with independent real Kimi calls:

| Strategy | Score | Required missing | Calls / replies | Model seconds | Blocking wait seconds |
|---|---:|---:|---|---:|---:|
| Synchronous parent | -14069.735930 | 385 | 2 / 1 | 51.639 | 53.712 |
| Background interpreter | -13986.443617 | 383 | 1 / 1 | 20.483 | 2.079 |

Both completed without planner errors. The +83.292313 difference includes model-delivery variability; it does not establish a stable score improvement. Normalized CPU increased from 231.209 to 243.524 seconds. The background answer was adopted almost six simulated hours after its request, so overlap can sacrifice early decisions. A separate direction-validation candidate scored -12792.643315 in this world; these are not identical-response comparisons.

Ten lifecycle checks cover one in-flight job, memory snapshots, main-thread updates, message provenance and worker failures. Model budgets remain 30 seconds per call, 120 total, 8 calls and 2200 output tokens. Formal eight-card results are pending.
