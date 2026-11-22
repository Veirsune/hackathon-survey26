# Agent Observer — Numerical scheduler

This branch runs the [GOSIM Agentic Observer Challenge](https://github.com/gosimfoundation/hackathon-survey26) using public survey feedback and a numerical planner. It runs locally without an API key.

## How it chooses an action

1. **Update the sky and instrument estimates.** The planner reads weather notices, active requests and the previous exposure. It tracks each target’s best observation and uses fibre hits to correct the next pointing. See [state](agent_core/state.py) and [pointing calibration](agent_core/pointing_calibration.py).
2. **Budget the search.** The [calendar governor](agent_core/calendar_governor.py) compares remaining observing time with CPU already spent. It uses measured search costs to select the amount of work to spend on the next decision.
3. **Plan an exposure.** The [scheduler](agent_core/search.py) compares pointings, fibre assignments and exposure durations. It weighs the expected improvement for each target against the time required and gives priority to required targets and expiring requests.
4. **Investigate low throughput.** If ordinary planning finds no useful exposure and throughput appears low, the planner can schedule a [short diagnostic measurement](agent_core/information_probe.py). Its observed result feeds back into the survey state. The [planner](agent_core/planner.py) checks the accumulated evidence and reporting allowance before requesting a repair.

## Run

```sh
python -m pip install -r requirements.txt
AGENT_LLM_ENABLED=0 python -u agent.py
```

The agent reads JSON Lines on stdin, writes one validated action per decision to stdout, and sends diagnostics to stderr.

[Formal evaluation](FORMAL_RESULT.md) · [Post-competition observer architecture](https://github.com/Veirsune/hackathon-survey26/blob/experiment/event-driven-kimi-20261019/README.md) · [License and attribution](LICENSE.md)
