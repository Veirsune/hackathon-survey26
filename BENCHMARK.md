# Local comparison

Official local L4: 8,800 targets, 440 required targets, 900-second budget. These are development measurements, not official alpha leaderboard scores.

## Current results

| Configuration | Score | Required misses | Observed targets |
| --- | ---: | ---: | ---: |
| Numerical, fixed margin 1.05 | 7057.062358 | 0 | 8408 |
| Kimi, current-margin policy previews | 7057.062358 | 0 | 8408 |

Both received 200 request reward and 100 report settlement, without reduced-search fallback. Kimi completed 6 successful, accepted reviews, spending 66.414 seconds on model calls. It retained balanced scheduling and margin 1.05 throughout, with zero control changes. All 1,095 executable actions matched the numerical control exactly, so this run demonstrates no score benefit from model assistance.

The numerical trial took 551.203 seconds on Windows. A Linux run with all model calls failing reproduced every one of its 1,095 executable actions and the exact score in 131.779 seconds; it is fallback evidence, not Kimi assistance. The current Kimi run took 191.041 seconds on Linux. Cross-host timing is not evidence of algorithmic speedup.

The default exposure margin is now 1.05. The offline branch retains this value across nights; the Kimi branch may revise it. Relative to margin 1.0 (6942.418765), fixed 1.05 gained 114.643593, with five fewer observed targets. Science gains across brightness quartiles, faintest first, were 62.44, 41.07, 7.83 and 3.45. Fixed 0.95 scored 6859.039357 and was rejected.

## Method

The numerical scheduler jointly selects fields, fiber assignments and exposure duration by predicted best-score improvement, with required-target and request completion rewards. It refines up to three distinct pointings and learns pointing corrections from public hit feedback. Ordinary science targets use nominal throughput; unfinished required/request targets retain a 0.90 discount, and the exposure margin applies to all targets.

A discrete sky/efficiency filter uses public scores to correct the final program declaration and interpret ambiguous feedback. Confirmed bonus scores take precedence. Its probabilities and thresholds are engineering estimates, not calibrated confidence levels. Policy previews use the corrected final program and current exposure margin, with matching metadata. The prompt identifies balanced/1.05 as the numerical baseline and explains that these short previews compare policies, not alternative margins.

Fault diagnosis uses public warnings and multi-night feedback, tracks free-report allowances, and permits at most one paid attempt per survey. The preceding feedback algorithm passed one synthetic no-fault check without paid reports or penalties; that is not a new check of this margin revision or a general false-positive estimate.

## Earlier model comparisons

The preceding Kimi version used margin-1.0 previews despite its initial margin of 1.05. It scored 7034.350445, changed the margin to 1.0 during the season, and observed 8402 targets. The current run is 22.711913 higher, but differing model answers prevent attributing this single-run difference causally to the preview and prompt correction.

At initial margin 1.0, corrected-preview Kimi scored 6967.144527 versus numerical 6942.418765 (+24.725762). Before the preview correction, a separate Kimi run scored 6981.341587. Different model answers and configurations prevent treating these as repeated measurements of one policy.

## Submission

Import this GitHub repository and choose `main` for Kimi or `no-llm` for the offline agent. The offline model client is disabled unconditionally. Neither branch contains credentials.

The user-provided older cloud alpha artifact scored 6808.269150 and accepted no model advice (HTTP 400). Its source commit was not recorded. The official proxy rejects `reasoning_effort`; the cloud manifest omits it. Current cloud results must be measured independently.
