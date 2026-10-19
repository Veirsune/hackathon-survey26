# Event-driven neural observer

Experimental survey agent combining an online neural observation planner, explicit instrument-work scheduling, and Kimi advice. Public work notices can trigger timely reports and shorten the planning horizon; unexplained losses use observation-based fault diagnostics.

Kimi interprets weather and engineering notes and advises on computed plans. Configure `OPENAI_API_KEY`, `OPENAI_BASE_URL=https://api.kimi.com/coding/v1`, and `OPENAI_MODEL=kimi-for-coding` in the platform. Model calls are bounded; no credentials are stored here.

Submit this branch with `observer.project.json` to the **after-party** phase. This is an experimental evaluation, not a selected final version.

The schedule parser is adapted through an integration layer from [Argelander](https://github.com/hou-physics/gosim2026-agentic-observer-argelander), pinned at `a98cb68324effbe11bc0d732ea519dafc4285edd`; its source is unchanged. See `LICENSE.argelander` and `PEER_RESEARCH.md`.
