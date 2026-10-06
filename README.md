# Survey Observer

A survey scheduling agent with Kimi-assisted station knowledge. Kimi reads delivered operator notes, resolves terrain measurements and corrections, and returns quoted evidence. The scheduler handles visibility, fiber assignment, exposure selection, and target priorities.

Run `python agent.py` using the competition JSONL protocol. Configure `KIMI_API_KEY`, `KIMI_BASE_URL`, and `KIMI_MODEL` (or the corresponding `OPENAI_*` variables) through the platform. Kimi Coding Plan requests omit temperature. Install dependencies from `requirements.txt`.

Official eight-card total: **224107.476323**. Seven cards completed; D1 hit the 3600-second wall limit. See [BENCHMARK.md](BENCHMARK.md) for the full result and limitations.

`AGENT_LLM_OUTPUT_LIMIT` controls response length (2200 by default in the manifest); model credentials belong in platform settings.
