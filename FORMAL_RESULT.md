# Official formal evaluation

Mean **30540.082335**, compared with **30500.0685825** for the matched Kimi configuration: +40.0137525 (+0.13%). Every card finished the full season with zero model calls, no planner errors, and no hard time cap.

| Card | Score | Difference from Kimi ON | Required missing |
|---|---:|---:|---:|
| A | 23993.165504 | +120.938984 | 1 |
| B | 39747.722886 | +138.067389 | 0 |
| C | 25530.185234 | -81.146344 | 0 |
| D | 32889.255716 | -17.805019 | 1 |

This configuration differs from the frozen Kimi parent only in the manifest's model-enable switch; runtime Python source is byte-identical. Disabling the expert also changes its control settings and CPU use. One evaluation per configuration does not establish a statistically reliable model effect; machine calibration differed as well.

Revision: `1041d358-48c4-4af3-a547-d8a057f6afe8`  
Batch: `4fce4103-8579-42a9-bb6c-855b494a9d26`  
Phase: official online A/B/C/D, 2026-10-05.

Source/result hashes were verified against the downloaded platform artifacts. The manifest disables models for platform execution; the optional client remains in the shared code and can be enabled by an explicit environment override during a manual run.
