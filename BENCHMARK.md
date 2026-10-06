# Local integration evidence

Only `agent_core/station_notes.py` changes relative to runtime commit `001140c`. Each claim must pass the existing exact-quote, schema, and numerical checks. Duplicate directions retain uncertainty when present; otherwise the most conservative existing execution bound is selected. No averaged or invented altitude is introduced. Invalid individual evidence still rejects the response.

Three sequential, real-Kimi runs used the same frozen public-A-derived 12-night world with an already delivered official D1 opening note:

| Variant | Score | Missing required targets | Model wait |
|---|---:|---:|---:|
| Strict parent | -17830.779994 | 451 | 58.760 s |
| Claim reconciliation (this branch) | -14069.735930 | 385 | 51.639 s |
| Reconciliation, reasoning disabled | -16539.357505 | 427 | 6.190 s |

All completed with zero planner errors. This branch improved by 3761.044064 in that single comparison. Model interpretations and trajectories varied, so the difference cannot be attributed entirely to reconciliation. The faster alternative regressed by 2469.621575 and is not included.

The note need not match the synthetic terrain; these are stress-test scores, not official D1 or hidden-card results. Fifteen mechanism checks cover actual duplicate responses, unchanged valid responses, unsupported evidence, uncertainty precedence, and bounded response size. Existing unit tests also pass. The shared merger passed a fresh multilingual correction/future/withdrawal check with the fast model, but that does not establish general model accuracy.
