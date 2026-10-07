# Evaluation notes

Research candidate derived from recovery baseline `3d82e84`. Online recursive least squares learns conditional log-score residuals from delivered observation results; model calls are optional. It does not read evaluator truth or identify the scenario by card name.

A complete local formal-A proxy season with Kimi disabled improved from 22264.25 to 24016.87 under the same 900-second normalized CPU budget. Required misses decreased from 3 to 1; both runs completed without planner errors. The learner updated on 3409 exposures and changed 265 candidate selections. Repair timing also changed, so this is a whole-agent comparison, not an isolated estimate of prediction-model benefit.

Independent transfer to a predeclared, newly generated formal-B proxy with shuffled target properties changed the score from 41504.06 to 41469.35 (-34.70, -0.084%). Both completed with zero required misses and no planner errors; normalized CPU was 818.23 and 856.97 seconds. Thus the large A gain did not transfer into a B gain. An independent official eight-card evaluation is needed before claiming a stronger entry. These are local synthetic-weather results, not official leaderboard scores or evidence of hidden-card performance. This branch has not replaced the final entry.
