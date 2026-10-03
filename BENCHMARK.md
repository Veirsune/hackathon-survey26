# Local L4 comparison

Both branches use public-feedback pointing calibration and a preference for observing difficult targets in good conditions (`calibrated_scarcity`). Kimi can retain or revise this policy (`expert_scarcity`); `no-llm` disables model transport unconditionally.

Official local runner, 900-second budget, 8,800 targets including 440 required targets.

| Run | Total score | Wall time (s) | Model calls |
| --- | ---: | ---: | ---: |
| no-llm | 6778.030889 | 432.937 | 0 |
| Kimi | 6778.030889 | 501.812 | 6 |

All 1,071 executable actions matched. Kimi kept the balanced plan at all six reviews; all responses were accepted, with 47.952 seconds of model waiting. This run shows no additional score benefit from model review and about 69 seconds of additional runtime, including previews. Other cards and future model responses may differ.

| Score component | Both runs |
| --- | ---: |
| Best target scores | 6478.616374 |
| Required-target penalty | 0 |
| Fault-report settlement | 100 |
| Uniformity penalty | -0.585485 |
| Observation-request reward | 200 |

Both runs completed both requests and all required targets, observed 8,316 targets in 965 exposures, and used no reduced-search fallback. The numerical change improved the previous local result by 53.153343 points; this gain must not be attributed to Kimi.

Model settings: `kimi-for-coding`, 30 seconds per call, 120 seconds total, at most 6 calls, reasoning effort `low` (provider-side effect unverified). Environment settings override defaults. Neither branch includes credentials.

These are single local L4 measurements, not official alpha leaderboard scores. Import the GitHub repository and select `main` or `no-llm` on the competition platform.
