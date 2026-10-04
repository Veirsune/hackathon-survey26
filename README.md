# Agent Observer

A Python agent for the [GOSIM 2026 Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26).

Kimi reviews weather, observation history, deadlines, and planning previews. A numerical scheduler selects pointings, fibre assignments, and exposures. Search depth adapts to the remaining observing calendar and CPU budget; expert processing costs are tracked separately.

## Run

```sh
python -m pip install -r requirements.txt
python -u agent.py
```

Set `OPENAI_BASE_URL=https://api.kimi.com/coding/v1`, `OPENAI_MODEL=kimi-for-coding`, and `OPENAI_API_KEY`. Keep the key in your environment or the platform's secret settings. See `.env.example` for optional limits.

Input and output use JSONL; logs go to stderr. Numerical scheduling continues if model calls fail.

This version scored **29,773.73** across formal A/B/C/D in one official evaluation. See [results](FORMAL_RESULT.md). The [no-model reference](https://github.com/Veirsune/hackathon-survey26/tree/formal-compute-off-29554) is preserved separately.

Based on the official Python example. See [LICENSE.md](LICENSE.md).
