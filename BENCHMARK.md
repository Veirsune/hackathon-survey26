# Local comparison

Official local L4: 8,800 targets, 440 required targets, 900-second budget. These are development measurements, not official alpha leaderboard scores.

## Preserved official alpha best (conditional paid recovery)

This branch is based on numerical-only `d3ffc0d`. The only algorithm change removes the unconditional seven-day wait after an incorrect report when the free allowance is exhausted. It retains the 48-hour spacing, additional 20% throughput-decline test before seven days, weather and earthquake exclusions, two-night evidence, remaining-time check, and one-paid-attempt limit. It does not include catalogue tile search.

| Official card | Fixed 1.05 baseline | This variant | Difference |
| --- | ---: | ---: | ---: |
| Alpha | 7130.666267 | **7450.404783** | +319.738516 |
| Beta | 6692.600743 | 6692.600743 | 0 |
| Gamma | 6848.184090 | 6848.184090 | 0 |
| Delta | 6786.172782 | 6786.172782 | 0 |

Official revision `5ff9b769-f43b-425b-967c-7d53ef593082`, batch `62bce89e-5c81-4f40-90fd-e2590e740f22`, used frozen `conditional_paid_recovery` with an unconditional offline client. Alpha repaired the instrument on October 24 rather than October 29, after 805 identical actions. The gain consists of +269.543695 science score, +50 from one fewer required miss, and +0.194820 uniformity. Alpha observed 9,502 targets, missed five required targets, and earned 200 request reward plus 100 report settlement. Beta, gamma and delta reproduced all 1,107 / 1,133 / 1,223 baseline actions respectively.

All runs used zero model calls, with no planner errors or reduced-search fallback. Alpha explicitly finished with only 15 seconds remaining in its final night; the other cards reported `survey_complete`. This is a single official scenario comparison, not a universal safety guarantee: a false paid report would cost 150. A no-fault stress comparison reproduced 1,117 actions with no paid report but did not exercise the newly allowed 48–168-hour interval. Ordinary local L4 remained 7057.062358 with all 1,095 baseline actions unchanged.

The earlier Kimi alpha best was 7302.987962. This branch preserves the independently tested numerical variant; combinations with catalogue tile search or model changes need separate evaluation.

## Earlier local results

| Configuration | Score | Required misses | Observed targets |
| --- | ---: | ---: | ---: |
| Numerical, fixed margin 1.05 | 7057.062358 | 0 | 8408 |
| Kimi, initial margin 1.05 | 7034.350445 | 0 | 8402 |

Both received 200 request reward and 100 report settlement, without reduced-search fallback. Kimi completed 6 successful, accepted reviews, spending 67.2 seconds on model calls. Its score was 22.711913 below the fixed policy in this single trial. It retained balanced scheduling and changed the margin from 1.05 to 1.0 during the season. This does not establish stable model benefit.

The numerical trial took 551.203 seconds on Windows. A Linux run with all model calls failing reproduced every one of its 1,095 executable actions and the exact score in 131.779 seconds; it is fallback evidence, not Kimi assistance. The successful Kimi run took 193.614 seconds on Linux. Cross-host timing is not evidence of algorithmic speedup.

The default exposure margin is now 1.05. The offline branch retains this value across nights; the Kimi branch may revise it. Relative to margin 1.0 (6942.418765), fixed 1.05 gained 114.643593, with five fewer observed targets. Science gains across brightness quartiles, faintest first, were 62.44, 41.07, 7.83 and 3.45. Fixed 0.95 scored 6859.039357 and was rejected.

## Method

The numerical scheduler jointly selects fields, fiber assignments and exposure duration by predicted best-score improvement, with required-target and request completion rewards. It refines up to three distinct pointings and learns pointing corrections from public hit feedback. Ordinary science targets use nominal throughput; unfinished required/request targets retain a 0.90 discount, and the exposure margin applies to all targets.

A discrete sky/efficiency filter uses public scores to correct the final program declaration and interpret ambiguous feedback. Confirmed bonus scores take precedence. Its probabilities and thresholds are engineering estimates, not calibrated confidence levels. Policy previews use the corrected final program; they currently compare policies at margin 1.0 and explicitly report that assumption. A current-margin preview revision is being investigated separately.

Fault diagnosis uses public warnings and multi-night feedback, tracks free-report allowances, and permits at most one paid attempt per survey. The preceding feedback algorithm passed one synthetic no-fault check without paid reports or penalties; that is not a new check of this margin revision or a general false-positive estimate.

## Earlier model comparisons

At initial margin 1.0, corrected-preview Kimi scored 6967.144527 versus numerical 6942.418765 (+24.725762). Before the preview correction, a separate Kimi run scored 6981.341587. Different model answers and configurations prevent treating these as repeated measurements of one policy.

## Submission

Import this GitHub repository and choose `main` for Kimi or `no-llm` for the offline agent. The offline model client is disabled unconditionally. Neither branch contains credentials.

The user-provided older cloud alpha artifact scored 6808.269150 and accepted no model advice (HTTP 400). Its source commit was not recorded. The official proxy rejects `reasoning_effort`; the cloud manifest omits it. Current cloud results must be measured independently.
