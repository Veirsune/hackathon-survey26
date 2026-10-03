# Agent Observer

A Python agent for the [GOSIM 2026 Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26).

Kimi reviews observation history, weather, deadlines, and short planning previews to choose a persistent observing policy. A numerical scheduler selects pointings, fiber assignments, and exposure times, with pointing calibration learned from public hit feedback. Accepted plans survive failed model calls and can be revised on later nights.

## Run

Python 3.9+; no third-party dependencies. Set these environment variables:

```dotenv
OPENAI_BASE_URL=https://api.kimi.com/coding/v1
OPENAI_MODEL=kimi-for-coding
OPENAI_API_KEY=your-api-key
AGENT_LLM_CALL_SECONDS=30
AGENT_LLM_TOTAL_SECONDS=120
AGENT_LLM_MAX_CALLS=6
AGENT_LLM_REASONING_EFFORT=low
```

See `.env.example`. Keep credentials local; direct execution reads environment variables, while the competition platform supplies them at runtime.

```sh
python -u agent.py
```

Input and output use JSONL with `participant-agent-protocol-v4`; logs go to stderr. Scheduling continues when model calls fail.

Best tested local L4 result: **6778.03**, with all required targets completed. See [benchmark details](BENCHMARK.md). This is a local project best, not an official leaderboard SOTA claim.

```sh
python -m unittest discover -s tests -v
```

The offline agent is on the [`no-llm` branch](https://github.com/Veirsune/hackathon-survey26/tree/no-llm). Import the repository in the competition platform and select the desired branch.

Based on the official Python example. See [LICENSE.md](LICENSE.md).
