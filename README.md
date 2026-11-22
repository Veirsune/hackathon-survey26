# Agent Observer

A Python telescope scheduler for the [GOSIM Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26). At each decision it uses the latest survey feedback to choose a field of view, assign targets to fibres and set an exposure time.

## Versions

| Version | How it makes decisions |
| --- | --- |
| [Post-competition observer](https://github.com/Veirsune/hackathon-survey26/blob/experiment/event-driven-kimi-20261019/README.md) | A dated queue of instrument work sets the next planning deadline. Numerical search generates exposures, an online neural model adjusts their ranking from observed returns, and Kimi interprets terrain and engineering notes when they arrive. |
| `main` (this branch) | Kimi periodically reviews the observing policy. A numerical scheduler chooses each exposure under that policy. |
| [Numerical observer](https://github.com/Veirsune/hackathon-survey26/blob/no-llm/README.md) | Calendar-based compute allocation controls search depth. Short diagnostic exposures help the agent investigate poor throughput. |

[Browse all branches](https://github.com/Veirsune/hackathon-survey26/branches).

## How main chooses an action

1. **Update the survey state.** On each decision request, the planner reads the latest bulletin, active requests and previous observation. It tracks each target’s best result and uses fibre hits to correct telescope pointing. See [state](agent_core/state.py) and [pointing calibration](agent_core/pointing_calibration.py).
2. **Review the policy.** At a review, Kimi sees observation history, deadlines, weather and short previews of candidate policies. It can change the priority given to required targets or expiring requests, adjust the exposure margin, or propose a fault report. The planner keeps the last accepted policy if a call fails. See [expert observer](agent_core/expert_observer.py).
3. **Choose the next exposure.** The scheduler compares candidate pointings, fibre assignments and exposure lengths by the improvement they could add over each target’s best result. It also accounts for required targets, request deadlines and the time each exposure would consume. See [search](agent_core/search.py) and [optimizer](agent_core/optimizer.py).
4. **Return one action.** The planner can observe, report a suspected fault, wait for an observing window, or finish the survey. The entry point validates the action and writes it to stdout. The next decision incorporates the resulting feedback. See [planner](agent_core/planner.py) and [entry point](agent.py).

## Run

Use Python 3.9 or later. For local Kimi reviews, set `OPENAI_BASE_URL`, `OPENAI_MODEL` and `OPENAI_API_KEY` in the process environment. The [example configuration](.env.example) also documents the call and time budgets.

```sh
python -u agent.py
```

The agent reads `participant-agent-protocol-v4` messages as JSON Lines on stdin and writes diagnostics to stderr. Run the tests with `python -m unittest discover -s tests -v`.

[Benchmark and evaluation notes](BENCHMARK.md) · [License and attribution](LICENSE.md)
