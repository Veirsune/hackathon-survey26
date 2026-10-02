# Agent Observer

A Python agent for the [GOSIM 2026 Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26).

The agent combines numerical observation scheduling with Kimi-assisted weather interpretation, candidate selection, and fault assessment. It tracks observation results across nights and retries failed model stages on later nights.

## Configuration

Set these environment variables using your own credentials:

```dotenv
OPENAI_BASE_URL=https://api.kimi.com/coding/v1
OPENAI_MODEL=kimi-for-coding
OPENAI_API_KEY=your-api-key
```

See `.env.example` for optional settings. Keep `.env` local. Direct execution reads environment variables; the competition platform supplies them at runtime.

## Run

Python 3.9+; no third-party dependencies.

```sh
python -u agent.py
```

The agent receives JSONL messages on stdin and writes decisions to stdout using `participant-agent-protocol-v4`. Logs go to stderr. If model calls fail, observation scheduling continues.

## Tests

```sh
python -m unittest discover -s tests -v
```

Based on the official Python example. See [LICENSE.md](LICENSE.md) for attribution and licensing.
