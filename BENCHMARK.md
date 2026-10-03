# Local comparison

The matched model comparison below measures the numerical baseline before the diagnostic extension described below.

Both branches use public-feedback pointing calibration, good-sky target preference, and exposure candidates at predicted program-band boundaries. Kimi can retain or revise the persistent observing policy; `no-llm` disables model transport unconditionally.

Official local runner, 900-second budget. L4 has 8,800 targets including 440 required targets.

| L4 run | Score | Wall time (s) | Model calls |
| --- | ---: | ---: | ---: |
| no-llm | 6809.415585 | 428.859 | 0 |
| Kimi | 6809.415585 | 523.375 | 6 |

All 1,079 executable actions matched. The model made 0 policy changes and spent 66.095 seconds waiting for responses. The measured model-on score difference is +0.000000; acceptance of model advice alone is not evidence of a score benefit.

| Score component | no-llm | Kimi |
| --- | ---: | ---: |
| Best target scores | 6510.097654 | 6510.097654 |
| Required penalty | -0.000000 | -0.000000 |
| Fault reports | 100.000000 | 100.000000 |
| Uniformity penalty | -0.682069 | -0.682069 |
| Request reward | 200.000000 | 200.000000 |

The numerical change improved L4 by 31.384696 points versus the previous release, with 0 required targets missing. An additional algorithm-only L1 check scored 6064.169749, up 29.420851, with 2 required targets missing. These numerical gains must not be attributed to Kimi. No full four-card rerun was performed.

Model settings: `kimi-for-coding`, 30 seconds per call, 120 seconds total, at most 6 calls, reasoning effort `low` (provider-side effect unverified). Environment settings override defaults. Neither branch includes credentials.

These are single local measurements, not official alpha leaderboard scores. Stress-test injections are excluded. Import the GitHub repository and select `main` or `no-llm` on the competition platform.

## Weather-aware fault diagnosis

Both branches now permit at most one report beyond the free allowance per survey. It requires a further persistent throughput decline, sufficient remaining observing time, and evidence from exposures without public all-sky weather warnings. Existing quake and multi-night checks remain in place.

- Ordinary L4: 6809.415585 points in 429.969 seconds, with all 1,079 actions identical to the numerical reference. The new paid path was not needed.
- Allowance-exhaustion stress: the rule retained the true-fault repair, gaining 1507.801600 points versus disabling further diagnosis.
- Synthetic no-fault stress: weather filtering avoided the previous 150-point false report; all 1,096 non-report actions were unchanged.

The stress tests used the preceding numerical baseline and are diagnostic experiments, not leaderboard scores or an estimated false-positive rate. No new model API run was performed for this diagnostic extension. The agent never reads the evaluator's hidden data.
