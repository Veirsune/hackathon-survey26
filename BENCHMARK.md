# Diagnostic retry experiment

Public formal A catalogue, instrument and scoring; 48-night synthetic weather, official CPU-clock runner. Sequential frozen baseline/candidate runs. These are not leaderboard scores.

| Late cause | Baseline | Candidate | Difference |
|---|---:|---:|---:|
| Instrument fault | 11428.290618 | 15096.784759 | +3668.494141 |
| Weather only | 11044.291761 | 11015.144064 | -29.147697 |

The candidate made one extra paid attempt in each case. It repaired the real fault and reduced required misses from 37 to 10. In the weather control it incurred an extra 150-point false-report penalty; unrelated trajectory differences offset part of that loss. All four runs completed without errors. Search trajectories differed before the retry, so total differences are not causal estimates of the report alone.

The retry budget permits at most two additional paid attempts, with 14-day then 28-day backoff after a paid false report. These synthetic cases target a known failure mode; they do not prove hidden-card generalization. Official evaluation is pending.
