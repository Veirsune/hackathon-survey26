# Validation

The previous diagnostic version regressed on official A, C and D after treating all-zero exposures as fault evidence. This branch excludes zero-score samples from the new diagnostic; existing reporting remains unchanged. It does not diagnose complete instrument blackout through this new path.

A 12-night local scenario with three severe recurring faults retained all three repairs and exactly matched the previous version's score components and counts: total -7802.291311, 277 required targets missing. The abbreviated season's negative total is not an official score.

The full local variable-weather A comparison completed with models OFF: parent 22297.449784, candidate 24067.982588 (+1770.532804); required misses 3 to 1; normalized CPU 674.546 to 708.043 seconds. Both completed without planner errors or timeout. The new diagnostic did not trigger in this full-season run, so its score difference is not a causal estimate of repair benefit; adaptive compute and subsequent observation paths can differ.

Official eight-card validation is pending. No hidden-card generalization claim is made.
