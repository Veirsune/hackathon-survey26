# Local deadline experiments

Frozen diagnostic baseline, sequential matched runs, unmodified official CPU-clock runner. Synthetic worlds; these are not leaderboard scores.

| Test | Baseline | Dual clock | Difference |
|---|---:|---:|---:|
| 12 nights, 60-second wall cap | -35317.506005 | -19409.959100 | +15907.546905 |
| 12 nights, 180-second wall cap | -19045.128018 | -18941.656576 | +103.471442 |
| Full public D calendar, synthetic weather | 30959.069027 | 31495.463896 | +536.394869 |

The baseline timed out in the 60-second stress case while the candidate completed. Both completed in the other two cases; the full D gain does not demonstrate timeout avoidance. Single paired runs and runtime-driven search trajectories limit causal attribution and generalization claims. Official eight-card evaluation is pending.
