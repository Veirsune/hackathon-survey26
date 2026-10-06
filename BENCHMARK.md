# Experimental results

This branch combines online terrain learning with bounded fault-report retries. It is an experimental candidate, not the selected final version.

A frozen 48-night synthetic scenario uses the official A catalogue and scoring, terrain obstruction, early unannounced weather deterioration and a later instrument fault. Changing only the report-budget module increased the score from 1322.409367 to 6669.619179 (+5347.209812). Missing required targets fell from 234 to 168. Both agents completed the season without planner errors.

The candidate made one additional paid report, which actually repaired the instrument. Both agents performed 24 terrain probes. The gain includes changed scheduling trajectories and is not attributed entirely to the report itself.

A separate report-only test previously gained 3668.494141 with a late fault but lost 29.147697 in weather-only conditions; that false report cost 150 points, partially offset by other scheduling changes. The combined terrain scenario has not yet repeated that weather-only control.

These are synthetic mechanism tests, not official leaderboard scores or evidence of hidden-card generalization. Official eight-card evaluation is pending.
