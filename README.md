# Survey observer

A Python survey agent with numerical pointing, fibre assignment and exposure planning, feedback calibration, and Kimi interpretation of station notices.

This research branch adds a bounded diagnostic for persistent catastrophic throughput loss. Failed diagnostics lock until normal throughput returns; extra paid false diagnostics are capped. It does not identify faults with certainty.

Import this GitHub branch using the competition platform and configure your Kimi service there. Kimi Coding Plan requests omit `temperature`. The project manifest installs its dependencies and starts `agent.py`.

See `BENCHMARK.md` and `FORMAL_RESULT.md` for validation status. No API keys are included.
