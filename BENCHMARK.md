# Local comparison

Both branches use feedback pointing calibration, shared-exposure optimization, program-boundary candidates, and full refinement around up to three distinct fields. Kimi can revise a persistent observing policy; `no-llm` disables model transport unconditionally.

Official local L4 runner: 8,800 targets, 440 required targets, 900-second budget. These are single local measurements, not official alpha leaderboard scores.

## Current numerical result

L4 model-off score: **6942.418765**, +9.012114 over the previous 6933.406651 control; runtime 541.578 seconds. Required misses: 0, request reward: 200, report settlement: 100. No reduced-search fallback or planner errors. Observed targets: 8,413, 38 fewer than the control; science score still increased by 9.077181. This single development-card improvement is small and does not establish an official alpha result.

A discrete sky/efficiency filter uses public per-target scores to correct the final program declaration and interpret ambiguous feedback from the same exposure. Confirmed bonus scores take precedence; otherwise only strong posterior mass changes the original feedback interpretation. Field selection and exposure search retain the previous objective. The model assumptions and probability thresholds are not calibrated confidence levels. Policy previews use the final corrected program and the same latent sky estimate; the numerical executor is unchanged by this preview consistency fix.

The same frozen numerical candidate completed the existing synthetic no-fault fixture without paid reports or report penalties. This is one weather trajectory, not an estimate of general false-positive risk.

## Current matched model comparison

| Corrected-preview L4 run | Score | Wall time (s) | Required misses |
| --- | ---: | ---: | ---: |
| Model disabled | 6942.418765 | 541.578 | 0 |
| Kimi enabled | 6967.144527 | 670.203 | 0 |

Kimi gained **24.725762** in this single run. All 6 calls succeeded and were accepted, using 77.937 seconds of model wait. Its 2 accepted policy changes selected requests priority and later returned to balanced; exposure margin stayed at 1.0. Both arms received 200 request reward and 100 report settlement, with no reduced-search fallback. Kimi observed 8,429 targets versus 8,413 and increased science score by 24.544896. The first 103 executable actions matched. The reused model-OFF control has the same numerical executor; only model-only preview code differs.

The preceding, uncorrected-preview Kimi run scored 6981.341587 (+38.922822), with one margin change to 1.05. These are different configurations and model responses, not repeated evidence of stable improvement or a causal estimate of the preview fix. Neither is an official alpha result.

## Previous numerical result

L4 model-off score: **6933.406651**, +21.010488 over the previous 6912.396163 control; runtime 550.797 seconds. Required misses: 0, request reward: 200, report settlement: 100. No reduced-search fallback or planner errors. Observed targets increased from 8,360 to 8,451.

Ordinary science targets now use nominal predicted throughput. Missing required targets and unfinished request targets retain the 0.90 completion discount. Geometry, direction attenuation, confidence, and the expert exposure margin remain in effect. Six search behavior tests and a mixed-obligation prediction check passed. This is one L4 development run, not a held-out result or an official alpha score.

Exact threshold memoization preserved all 1,124 executable actions and the score while reducing measured runtime from 593.375 to 550.797 seconds (42.578 seconds, 7.2%). Both runs used full search throughout. The cache distinguishes altered throughput, quality curves, thresholds, and time bounds. This is one timing comparison, not a science-score gain.

No separate Kimi run was made for the 6933.406651 numerical revision. The older matched comparison below belongs to the 6912.396163 version.

## Previous matched model comparison

| L4 run | Score | Wall time (s) | Model calls | Required misses |
| --- | ---: | ---: | ---: | ---: |
| Model disabled | 6912.396163 | 555.391 | 0 | 0 |
| Kimi enabled | 6844.513650 | 670.516 | 6 | 0 |

The first 98 executable actions matched; later actions diverged. Kimi made 2 accepted policy changes and spent 77.658 seconds waiting for responses. Its measured score difference was -67.882513. A policy change or accepted response alone does not establish a score benefit. Reduced-search fallback: disabled arm false, Kimi arm false.

Accepted expert reviews: 5 of 6 calls. Response statuses: invalid_json: 1, ok: 5. Unaccepted replies do not replace the active plan.

| Score component | Model disabled | Kimi enabled |
| --- | ---: | ---: |
| Best target scores | 6613.015551 | 6545.548781 |
| Required penalty | -0.000000 | -0.000000 |
| Fault reports | 100.000000 | 100.000000 |
| Uniformity penalty | -0.619388 | -1.035131 |
| Request reward | 200.000000 | 200.000000 |

## Numerical change

Full refinement around additional fields improved the numerical L4 score from 6882.569532 to 6912.396163 (+29.826631), with 44 more observed targets and no required misses. These gains belong to the numerical search, not Kimi. The initial experiment took 629.797 seconds. Composing it with the published gain cache and diagnostic rules preserved all 1,076 actions and reduced runtime to 555.391 seconds. Timing varies with the host; no full four-card rerun was performed.

## Diagnostic behavior

Free diagnosis can use calibrated pointing evidence on days 4-7 after a public earthquake. Weather-filtered multi-night evidence, sufficient remaining observing time, and a seven-day cooldown constrain paid diagnosis to at most one attempt per survey. The extra comparison against an old false report expires after seven days, avoiding permanent lockout after an unusually low weather reading.

Separate recovery and synthetic no-fault experiments support these guards: expiring the old comparison restored a missed repair in a losing control, while its no-fault repeat made no paid reports. These experiments are not leaderboard scores or an estimated false-positive rate. No injected reports, hidden weather, or evaluator files are used by the submitted agent.

## Model and submission

Kimi settings: `kimi-for-coding`, 30 seconds per call, 120 seconds total, at most 6 calls, reasoning effort `low` (provider-side effect unverified). Public evidence, short nominal policy previews and the observer notebook guide reviews. Accepted plans persist between reviews; policy previews do not alter the actual score ledger. Network latency and model outputs can vary.

Neither branch includes credentials. Import the GitHub repository and select `main` for Kimi or `no-llm` for the offline agent.

## Uploaded cloud artifacts

The user-provided practice runs scored alpha 6808.269150, beta 6784.796983, gamma 6875.368955, and delta 6518.678848. Their source commit is not recorded in the artifacts. Each attempted one model call, received HTTP 400, and accepted no advice; they do not measure working Kimi assistance.

The official proxy rejects `reasoning_effort` as an unsupported chat option. The main cloud manifest now omits that setting; direct local tests above used it. This fixes a verified request-contract conflict, but a successful cloud call after the fix has not yet been observed.
