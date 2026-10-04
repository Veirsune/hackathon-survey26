# Local comparison

Latest numerical L4 reference: **6882.569532**, up **73.153947**. The latest diagnostic change has no fresh Kimi API run; the matched model comparison below remains the earlier reference.

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

## Reused exposure gains

The numerical optimizer now reuses matched/mismatched gains across overlapping pointings while applying each pointing's confidence separately. An algorithm-only L4 run retained all 1,079 reference actions and 6809.415585 points, taking 395.141 seconds versus 428.859 seconds for the reference (33.718 seconds saved). These are single timing measurements; no additional model API timing was measured. Weather-aware diagnostic behavior is unchanged.

## Earlier diagnosis after pointing recovery

During days 4-7 after a public earthquake notice, the free-report fallback can diagnose earlier if recent fiber membership supports stable pointing, current sky warnings are absent, and two nights of weather-filtered evidence show a strong throughput drop. Paid-report limits and behavior outside this window are unchanged.

- Normal L4: **6882.569532**, versus 6809.415585; science increased by 73.050834 points. Required misses remained 0, request reward 200 and report settlement 100. Runtime was 429.562 seconds versus 429.969 for the control, with no search fallback.
- Correct repair moved from December 13 at 01:17:02 UTC to December 10 at 01:26:25 UTC. The earlier free false report was unchanged.
- Matched synthetic no-fault control: both scored 6964.742795, with identical actions and two free false reports, zero paid reports and no report cost. No reports were injected. This one weather trajectory does not establish a general false-positive rate; its scores are not official-card results.

The normal trial used the pre-cache numerical optimizer. The published branches retain the separately validated equivalent gain cache. No new combined-season timing or model-on score is claimed for this extension. Both branches include portable diagnostic tests; model transport settings are unchanged.

## Expiring stale diagnostic comparisons

The comparison against the last false report now expires after seven days, including when the free allowance is exhausted. A very low reading from an old false report no longer permanently prevents a later repair. The successful four-day free-report guard, weather evidence, seven-day paid cooldown, remaining-time requirement and one-paid-attempt seasonal cap remain in place.

A recovery experiment on a deliberately more aggressive free-report policy improved from 5270.229289 to 6809.415585 after a correct paid-channel repair. Its synthetic no-fault repeat completed in 442.515 seconds with two free false reports, zero paid reports and zero report cost. The first no-fault attempt was interrupted by confirmed Windows sleep and excluded. These tests establish recovery in the measured cases, not a new best score or a general false-positive rate.

Only the comparison-expiry condition is integrated here; the failed aggressive free-report policy is excluded. Targeted tests cover the composed policy and its retained limits. The normal 6882.569532 reference did not exhaust the free allowance, so this paid-path change was not exercised in that run. No new full-season composition timing or model-on result is claimed.
