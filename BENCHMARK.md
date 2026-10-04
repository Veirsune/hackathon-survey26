# Benchmark results

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

## Official practice results

Measured on the same official scenario fingerprints, using direct Kimi Coding access. Algorithm commits are shown; later documentation commits do not change these snapshots.

| Card | No LLM `d3ffc0d` | Kimi `8f1d573` | Kimi `914d4e7` |
| --- | ---: | ---: | ---: |
| Alpha | 7130.666267 | **7302.987962** | 7130.666267 |
| Beta | 6692.600743 | 6692.600743 | 6692.600743 |
| Gamma | 6848.184090 | 6969.541174 | **6991.339574** |
| Delta | 6786.172782 | **6850.113752** | 6786.172782 |

All runs completed within the official 900-second accounted budget without reduced-search fallback. Alpha's best version is preserved at tag [`cloud-alpha-7302`](https://github.com/Veirsune/hackathon-survey26/tree/cloud-alpha-7302); it remains 752.513624 below the verified 8055.501586 reference.

In `8f1d573`, Kimi changed alpha's margin to 1.0 at the first review, avoiding three required misses and adding 22.25 science points. In `914d4e7`, alpha, beta and delta retained balanced/1.05 and matched every no-LLM action. Gamma switched to requests then back to balanced, gaining 143.16 over no LLM. The preview correction therefore did not improve every card. Single stochastic model runs do not establish repeatable superiority.

Both Kimi batches left `reasoning_effort` unset. A separate same-code low-effort comparison is in progress; no score from that test is claimed here.

## Submission

The platform imports the repository default branch (`main`). To evaluate `no-llm`, upload an archive of that committed branch; branch URLs are currently unsupported. The offline model client is disabled unconditionally. Neither branch contains credentials.

The older user-uploaded alpha artifact scored 6808.269150 and accepted no model advice (HTTP 400); its source commit was not recorded. Those proxy failures are separate from the successful direct Kimi Coding runs above. Credentials are configured through the platform environment, outside this repository.
