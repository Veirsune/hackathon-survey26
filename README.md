# Agent Observer

A Python agent for the [GOSIM Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26).

Kimi reviews weather, observation history, deadlines, and numerical planning previews. The scheduler chooses pointings, fibre assignments, and exposures. Search depth follows the observing calendar and actual CPU expenditure.

## Run

```sh
python -m pip install -r requirements.txt
python -u agent.py
```

Set `OPENAI_BASE_URL=https://api.kimi.com/coding/v1`, `OPENAI_MODEL=kimi-for-coding`, and `OPENAI_API_KEY` in your environment or platform secrets. Input/output use JSONL; logs go to stderr. Numerical scheduling continues if model calls fail.

This version scored **30,500.07** across formal A/B/C/D in one official evaluation. See [results](FORMAL_RESULT.md). A prior [no-model reference](https://github.com/Veirsune/hackathon-survey26/tree/formal-compute-off-29554) is available; it uses an older CPU controller.

Based on the official Python example. See [LICENSE.md](LICENSE.md).
