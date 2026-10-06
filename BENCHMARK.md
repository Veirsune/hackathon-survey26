# Local evidence

Two completed 12-night synthetic worlds derived from public formal A. Both arms use real Kimi calls; the frozen control is the previous boundary-probe strategy. This change only updates terrain evidence aggregation.

| Station note | Control | Candidate | Difference | Missing required targets |
|---|---:|---:|---:|---|
| Overestimates horizon | -18123.717393 | -16209.835592 | +1913.881801 | 473 → 435 |
| Correct horizon | -12813.240769 | -12954.054259 | -140.813490 | 370 → 372 |

Both runs completed with no planner errors and one successful model response. Actual non-probe observations below the prior reached 394 distinct targets in the overstated world and 3 in the correct world. These observations demonstrate revision of the prior, not an attribution of every score change.

31 existing unit checks and 9 evidence-independence/consistency checks pass. One inherited test fixture needed its missing calendar governor initialized; runtime was unchanged.

The correct-note case regressed. Weather, changing terrain, narrow angular obstructions, and hidden-card generalization remain unproven. These scores are not official leaderboard scores; formal eight-card evaluation is required. This branch does not select the platform final version.
