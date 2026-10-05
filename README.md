# Survey Observer

A survey scheduling agent with Kimi-assisted station knowledge. Kimi reads delivered operator notes, resolves terrain measurements and corrections, and returns quoted evidence. The scheduler handles visibility, fiber assignment, exposure selection, and target priorities.

Run `python agent.py` using the competition JSONL protocol. Configure `KIMI_API_KEY`, `KIMI_BASE_URL`, and `KIMI_MODEL` (or the corresponding `OPENAI_*` variables) through the platform. Kimi Coding Plan requests omit temperature. Install dependencies from `requirements.txt`.

This experimental branch has passed a local 12-night synthetic comparison. Official eight-card performance is pending.
