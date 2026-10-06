# Local integration evidence

All runs below completed on frozen public-A-derived 12-night worlds, with real Kimi calls and no planner errors.

| Check | Frozen control | Control score | Integrated score | Difference |
|---|---|---:|---:|---:|
| Zenith note | Bracket learning without unit interpretation | -16081.633304 | -12704.001848 | +3377.631456 |
| Zenith note | Unit interpretation without bracket learning | -12559.902643 | -12704.001848 | -144.099205 |
| Falsely low literal altitude | Bracket learning without unit interpretation | -15126.975753 | -15126.975753 | 0 |

The direct unit-module comparison reduced missing required targets 433 → 367. Both arms made one successful model call; the integrated agent accepted a 49.5-degree zenith limit as a 40.5-degree altitude lower bound. The literal-altitude regression had byte-identical decisions and observations.

The second row records the exploration cost; combining mechanisms is not universally better. The controls differ between rows, so their deltas must not be pooled. Historical controls, model responses, and machine timing may vary. These are synthetic results, not official or hidden-card scores.

31 existing unit tests pass. Terrain and angle mechanisms also retain their separately documented evidence checks. The deployed runtime matches the frozen integration candidate; only the inherited unit-test fixture differs.
