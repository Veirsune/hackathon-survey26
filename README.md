# Survey Observer

A survey26 agent combining Kimi station-note interpretation, numerical scheduling, and observation-based terrain feedback. It converts explicit zenith angles to altitude bounds and uses bounded diagnostic retries after persistent throughput loss.

Configure model credentials in the platform settings. Kimi Coding Plan requests omit `temperature`; the manifest installs dependencies and runs the JSONL agent.

This experimental branch trades limited false-report risk for recovery from later faults. See [BENCHMARK.md](BENCHMARK.md) for both outcomes.
