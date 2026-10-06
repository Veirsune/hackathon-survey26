# Survey Observer

A survey26 agent combining Kimi station-note interpretation, numerical scheduling, and observation-based terrain feedback. Explicit zenith angles are converted into verified altitude bounds. Independent observations can revise uncertain terrain estimates.

Configure model credentials in the platform settings. Kimi Coding Plan requests omit `temperature`; the manifest installs dependencies and runs the JSONL agent.

This is an experimental integration. See [BENCHMARK.md](BENCHMARK.md) for measured benefits, regressions, and the different controls used.
