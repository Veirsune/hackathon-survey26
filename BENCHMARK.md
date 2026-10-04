# Official practice result

This unconditional no-LLM agent adds a bonus-based fault diagnostic to conditional paid recovery. It does not include catalogue tiles.

| Card | Total | Required missing |
| --- | ---: | ---: |
| Alpha | 7500.705805 | 5 |
| Beta | 6692.600743 | 11 |
| Gamma | 6848.184090 | 5 |
| Delta | 6786.172782 | 7 |

Official batch: `66627193-8adc-45ab-87cc-a5f04ef05182`; revision: `0bfab1ec-1f1f-45a5-b13d-3c26e96bbb03`.
Source digest: `5eee33930bbc56466223c188338f7816390801790eb68969e56100b9b498d0e5`.
Runtime files and manifest are byte-identical to the evaluated OFF source. Frozen source: `bonus_certified_diagnostic`, parent `conditional_paid_recovery`; only unconditional OFF transport and manifest setting were adapted for submission.

Alpha gained 50.301022 over its 7450.404783 parent: science +50.527140, uniformity -0.226117, unchanged required/report/request settlement. The correct repair at 2026-10-23 05:39:43 UTC preceded the parent by 19:55:51; the first 793 executable actions match. Targets observed increased from 9502 to 9513, with five required targets still missing. Beta, Gamma and Delta match the parent's complete action sequences and scores. All four runs made zero model calls, with no planner errors or fallback. Local L4: 7057.062358, unchanged from the parent.

The diagnostic uses repeated confirmed DARK exposures to infer low effective throughput; its nominal-efficiency assumption is not a universal physical guarantee. The independent catalogue-plus-conditional variant scored 7482.470151 on alpha and higher on the other cards; that comparison changes two mechanisms and does not establish additive gains.

Resolved official image: `python@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d`. The older conditional parent used a different platform image. Team environment was unchanged.
