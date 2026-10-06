# Engineering interpretation capacity

Parent: `20d6f20794aba1154f12c49d5855cb4d71699341`. Only the engineering interpreter budget changes: 8 calls/120 seconds to 16 calls/240 seconds. The existing station interpreter remains at 8/120; single calls remain limited to 30 seconds. Scheduling and diagnostic rules are unchanged.

| Sequential real-Kimi experiment | Parent | Candidate |
|---|---:|---:|
| Synthetic 24-night total score | 3627.472652 | 4474.523984 |
| Correct repairs / six injected faults | 5 | 6 |
| Missing required targets | 132 | 121 |
| False reports | 0 | 0 |
| Model calls / responses | 8 / 8 | 12 / 12 |

Both runs completed without errors. The +847.051332 difference includes +196.855802 science, +550 required-target penalty recovery, +100 reporting, and +0.195530 uniformity. This targeted public-A synthetic case uses twelve simple engineering announcements and is not an official or independent generalization score.

A separate chronological replay of actual A1 notices increased pre-event interpretation coverage from 2/6 to 4/6. The candidate still missed two notices and incurred five timeouts. More interpretation capacity does not guarantee score gains; false announcements and weather can still produce false reports. Longer waits can affect wall-clock limits.

Validation: four budget-boundary checks and the existing 20 client tests; complete local artifacts are retained in the research workspace.
