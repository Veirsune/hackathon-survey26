# Survey Observer

A Python survey agent that learns score-prediction errors from observation feedback and uses them to rank feasible observations. Fibre geometry, request handling, and fault recovery remain in the physical planner. Optional Kimi configuration uses the existing model-service environment variables.

Run `python -u agent.py`. The platform supplies JSON Lines through standard input.

See [evaluation notes](FORMAL_RESULT.md) for tested results and limitations.
