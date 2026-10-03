# Local L4 comparison

Both branches now use the same calibrated numerical base (`request_calibrated`). The Kimi branch adds persistent expert review (`expert_calibrated`); the offline branch disables model transport unconditionally.

Official local runner, 900-second budget, 8,800 targets including 440 required targets.

| Run | Total score | Wall time (s) | Model calls |
| --- | ---: | ---: | ---: |
| no-llm | 6724.877546 | 414.859 | 0 |
| Kimi | 6724.877546 | 529.671 | 6 |

All executable actions matched. Kimi accepted the balanced plan at all six reviews; all responses were valid, with 88.750 seconds of model waiting. This run shows no score benefit from model review and about 115 seconds of additional runtime, including preview computation and model waiting. It does not establish equivalence on other cards or future model responses.

| Score component | Both runs |
| --- | ---: |
| Best target scores | 6425.377041 |
| Required-target penalty | 0 |
| Fault-report settlement | 100 |
| Uniformity penalty | -0.499495 |
| Observation-request reward | 200 |

Both runs completed both requests and all required targets, observed 8,294 targets in 977 exposures, and used no reduced-search fallback. Public-feedback pointing calibration achieved a 99.74% fiber hit rate (12860/12893).

Model settings: `kimi-for-coding`, 30 seconds per call, 120 seconds total, at most 6 calls, reasoning effort `low`. Its provider-side effect is unverified. Explicit environment settings override defaults. Neither branch includes credentials.

These are single local L4 measurements, not official alpha leaderboard scores. Numerical calibration improved the earlier 6560.712756 result; that improvement must not be attributed to Kimi.
