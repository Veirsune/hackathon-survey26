# Survey Observer

A survey26 agent combining Kimi station-note interpretation, numerical scheduling, and observation-based terrain learning.

It uses two independent exposures to revise conservative terrain estimates. Lower blocked and higher successful targets can establish a local horizon interval. Model calls and exploration have fixed budgets.

Configure `KIMI_API_KEY`, `KIMI_BASE_URL`, and `KIMI_MODEL` through the platform model settings. Kimi Coding Plan requests omit `temperature`. The manifest installs dependencies and starts `agent.py` using the JSONL protocol.

This is an experimental branch. See [BENCHMARK.md](BENCHMARK.md) for measured improvements and regressions.
