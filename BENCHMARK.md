# Local validation

Compared with the frozen station-note baseline on public-A-derived 12-night worlds using real Kimi calls:

| Note | Baseline | Candidate | Difference | Missing required targets |
|---|---:|---:|---:|---|
| Zenith angle | -19031.433906 | -12559.902643 | +6471.531263 | 490 → 365 |
| Literal altitude | -12741.579803 | -12741.579803 | 0 | 367 → 367 |

The zenith candidate accepted the stated 49.5-degree zenith limit as a 40.5-degree altitude floor after one successful call. The baseline received eight JSON responses but accepted none. The literal-altitude candidate used one successful call; its decisions.csv and observations.csv were byte-identical to the frozen baseline. All runs completed without planner errors.

31 existing tests and 11 angle/evidence checks pass. Cloud packaging retains the previously verified OUTPUT_LIMIT environment alias; both local and cloud configurations select 2200 output tokens.

These are synthetic mechanism tests, not official scores. Only the station-note module changes relative to the official parent runtime. This branch does not include the separate bracket-learning experiment. Broader wording, weather, and hidden-card performance remain to be tested.
