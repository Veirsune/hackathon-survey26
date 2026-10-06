# Engineering forecast experiment

Frozen parent: `154c88c23f07c1a10e5f7e2a1c4c0520367f992a`. Sequential tests use the public A catalogue and two synthetic 24-night worlds, not official weather or full-season scores.

| World | Parent | Candidate | Difference |
|---|---:|---:|---:|
| Announced instrument faults | 3892.635489 | 4525.312317 | +632.676828 |
| False announcements with weather loss | -3015.184559 | -2752.337352 | +262.847207 |

All four runs completed with no planner errors. The candidate made two successful Kimi calls in each world. In the fault case it repaired both faults roughly 23 hours earlier and missed four fewer required targets. In the weather case it made three false reports versus two, including one paid false report (-150); a higher total score does not validate its diagnoses.

Engineering interpretation has a separate limit of 8 calls/120 seconds, in addition to the existing 8/120 budget. The new diagnostic path permits at most two paid attempts per season. Longer model waits may aggravate the parent's observed D1 wall-clock truncation. Corrections depend on grounded model interpretation; hidden-card generalization remains unproven.

Validation: 15 focused runtime checks and 31 existing unit tests. The first parent run completed successfully but its wrapper rejected truncated model-startup logs with zero calls; the result was retained without a rerun. Later wrappers record a non-secret configuration-presence boolean.
