# Local integration evidence

This branch adds bounded reporting retries to commit `001140c8fdfdb11f3fde1a24db518f05f96d03c4`. Only `agent_core/report_budget.py` changes at runtime. After an inconclusive paid report, up to two additional paid reports may occur, with 14- then 28-day backoff, sustained degradation checks, weather exclusions, and sufficient remaining observing time.

| Frozen 48-night synthetic world | Control | Candidate | Difference | Paid reports |
|---|---:|---:|---:|---|
| Terrain and late instrument fault | 3362.950676 | 8650.378864 | +5287.428188 | 1 → 2; second repaired the fault |
| Terrain and weather attenuation only | 2871.598903 | 2106.540943 | -765.057960 | 1 → 2; second was false |

Both pairs used the official CPU-clock runner, identical world files within each pair, and sequential execution. All four runs completed with zero planner errors. Model calls were disabled to isolate reporting/terrain interactions, so this is not evidence of a model contribution. Required targets missed changed 197 → 136 in the fault case and 202 → 214 in the weather case. The weather regression includes an additional 150-point false-report penalty and trajectory differences; the entire regression cannot be attributed to that penalty.

The candidate runtime matches the frozen local candidate. The 31 existing unit tests passed during packaging. These are synthetic checks, not official or hidden-card scores; neither case is a claim of universal improvement. The prior angle/terrain integration evidence remains in repository history.
