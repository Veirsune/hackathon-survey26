# Agent Observer — No LLM

Numerical agent for the [GOSIM Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26). It jointly chooses telescope pointings, fibre assignments and exposures, with calendar-based CPU allocation.

Model calls are disabled by `observer.project.json`. For a manual run:

```sh
python -m pip install -r requirements.txt
AGENT_LLM_ENABLED=0 python -u agent.py
```

Input/output use JSONL; logs go to stderr. No API key is needed.

Official A/B/C/D mean: **30,540.08**, with zero model calls. The matched [Kimi version](https://github.com/Veirsune/hackathon-survey26/tree/formal-feedback-pacing-kimi-30500) scored 30,500.07. These are single evaluations; see [results](FORMAL_RESULT.md).

Based on the official Python example. See [LICENSE.md](LICENSE.md).
