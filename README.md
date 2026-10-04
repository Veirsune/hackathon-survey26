# Agent Observer - No LLM

Offline numerical agent for the [GOSIM 2026 Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26).

This branch uses joint pointing, fiber assignment and exposure optimization, fixed request priority, fault diagnosis, and pointing calibration learned from public hit feedback. The model client is replaced with a disabled stub: API keys and model-enable environment variables cannot activate model calls.

Python 3.9+; no third-party dependencies or API configuration.

```sh
python -u agent.py
python -m unittest discover -s tests -v
```

Fault diagnosis uses public weather warnings and allows at most one report beyond the free allowance per survey.

Input/output: JSONL, `participant-agent-protocol-v4`. Logs go to stderr.

Best tested numerical L4 score: **6912.40**, with 0 required targets missing. See [benchmark details](BENCHMARK.md).

Use [`main`](https://github.com/Veirsune/hackathon-survey26/tree/main) for the Kimi agent, or this `no-llm` branch for the offline agent. Import the GitHub repository in the competition platform and select the desired branch.

Based on the official Python example. See [LICENSE.md](LICENSE.md).
