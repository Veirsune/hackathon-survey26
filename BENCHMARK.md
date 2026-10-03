# Local L4 benchmark

The released strategy is `expert_persistent`, tested with the official local runner and a 900-second budget. L4 contains 8,800 targets, including 440 required targets. These results are not directly comparable to the official alpha leaderboard.

| Strategy | Total score | Wall time (s) | Model calls |
| --- | ---: | ---: | ---: |
| Same numerical scheduler, model disabled | 6431.268346 | 511.422 | 0 |
| Fixed good-sky preference | 6473.060165 | 541.344 | 0 |
| Fixed request priority (2x) | 6560.712756 | 559.422 | 0 |
| Released Kimi observer | **6560.712756** | 688.266 | 6 |

The fixed request-priority control reproduced all 1,110 executable actions of the Kimi run. Thus this experiment shows no additional score advantage from runtime Kimi over that stronger static control. Model responses vary; one run does not establish generalization or statistical superiority.

## Released run

| Component | Points |
| --- | ---: |
| Best target scores | 6261.188239 |
| Required-target penalty | 0 |
| Fault-report settlement | 100 |
| Uniformity penalty | -0.475483 |
| Observation-request reward | 200 |
| **Total** | **6560.712756** |

Observed 8,184 unique targets in 1,003 exposures; zero required targets missing. Both observation requests completed. No reduced-search fallback was used.

Kimi configuration: `kimi-for-coding`, 30 seconds per call, 120 seconds total, at most 6 calls, reasoning effort `low`. All 6 calls returned JSON; 5 reviews were accepted, with 73.156 seconds spent waiting for the model. The runtime effect of the provider's reasoning-effort parameter has not been established.

Scheduling and prompts match the frozen measured strategy. The release changes the default call count from 8 to the tested value of 6; explicit environment settings override defaults. Credentials and full runtime traces are excluded from this repository.
