# Local L4 benchmark

Frozen strategy: `request_calibrated`. Official local runner, 900-second budget, 8,800 targets including 440 required targets.

| Component | Points |
| --- | ---: |
| Best target scores | 6425.377041 |
| Required-target penalty | 0 |
| Fault-report settlement | 100 |
| Uniformity penalty | -0.499495 |
| Observation-request reward | 200 |
| **Total** | **6724.877546** |

Wall time: 414.859 seconds. Model calls: 0. Both requests completed; 977 exposures, 8,294 targets observed, no reduced-search fallback.

Against the same fixed-request strategy without pointing calibration, score rose from 6560.712756 to 6724.877546. Fiber hit rate rose from 94.56% (12578/13301) to 99.74% (12860/12893). The trajectories differ, so this is an aggregate run comparison, not a matched-exposure causal estimate.

This branch preserves the measured numerical code and replaces the disabled API client with an unconditional offline stub. No credentials are required or read. This is one local L4 run, not an official alpha leaderboard result or a generalization claim.

The earlier Kimi release on main scored 6560.712756 without this calibration feature. That comparison mixes algorithm and model changes. A calibrated Kimi comparison is being evaluated separately; only matching numerical bases isolate the effect of Kimi.
