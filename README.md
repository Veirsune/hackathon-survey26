# Survey Observer

A survey scheduling agent with Kimi interpretation of station notes and engineering announcements. Geometry, exposure allocation, and bounded fault diagnostics run locally.

Run with `python agent.py`. Configure an OpenAI-compatible service using `KIMI_API_KEY`, `KIMI_BASE_URL`, and `KIMI_MODEL` (or the corresponding `OPENAI_*` variables). Kimi Coding Plan requests omit temperature. Set `AGENT_LLM_ENABLED=0` to disable model calls.

The platform builds and runs the project through `observer.project.json`. This research branch adds grounded engineering forecasts and checks subsequent exposure feedback before reporting a fault. It is not the selected final version. See [BENCHMARK.md](BENCHMARK.md) for results and limitations.
