# Local evidence

Only state feedback handling and the new `zero_patch.py` module change relative to commit `2080e72`. At least three real assigned hits, all exactly zero and with positive target flux/weight, activate a temporary spatial penalty. Missing hits do not count. Up to 80 positions are retained for ten minutes, using the existing 12-degree azimuth / 3-degree altitude neighborhood and 0.2 soft priority factor. This does not infer a permanent terrain boundary or instrument fault.

| Frozen 12-night synthetic world | Parent | Candidate | Difference | Required missing |
|---|---:|---:|---:|---|
| Terrain with conflicting station note, real Kimi | -14069.735930 | -16245.575938 | -2175.840008 | 385 → 436 |
| Transient weather closure/recovery, model disabled | -20661.736114 | -15640.405155 | +5021.330959 | 494 → 408 |

All four runs completed with zero planner errors. In the first comparison, the parent received one valid model reply while all four candidate calls timed out. This is a real system regression, but it does not isolate the feedback code. The second pair explicitly disabled models, used identical world files and the official CPU-clock runner, and gained 720.466848 science points plus 4300 required-target penalty points.

Six mechanism checks cover real-hit eligibility, positive feedback, expiry and bounded memory. Existing unit tests pass. These are synthetic local results, not official or hidden-card scores; no universal improvement is claimed.
