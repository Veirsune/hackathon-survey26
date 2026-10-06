# Survey Observer

A survey scheduling agent with Kimi interpretation of station and engineering notes. Geometry, exposure allocation, and fault diagnostics run locally.

Run `python agent.py`. Configure `KIMI_API_KEY`, `KIMI_BASE_URL`, and `KIMI_MODEL` (or corresponding `OPENAI_*` variables). Kimi Coding Plan requests omit temperature. Set `AGENT_LLM_ENABLED=0` to disable model calls.

The platform uses `observer.project.json`. See [BENCHMARK.md](BENCHMARK.md) for this research branch’s evaluation.
