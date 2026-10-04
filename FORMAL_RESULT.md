# Formal compute Kimi official result

One online batch, 2026-10-05 UTC+8: mean **29598.417005**, +11642.978554 versus frozen OFF baseline17955.438451. Revision `cf6e82c0-a40b-47cd-8fc8-d5c7435b5338`; batch `2f6fbb72-2f70-42c7-a53a-82e056bd7ced`. All downloaded CSV/message hashes verified.

| Card | Score | Delta OFF | Charged CPU | Wall seconds | Required missing | Nights reached | Kimi calls / accepted / policy changes |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 22929.376421 | -22.751298 | 784.188 | 1172.962 | 1 | 123/123 | 6 / 5 / 4 |
| B | 38613.262861 | +39540.997818 | 818.096 | 1190.670 | 0 | 183/183 | 6 / 4 / 2 |
| C | 24184.982919 | +6039.676417 | 877.285 | 1168.542 | 0 | 121/121 | 6 / 6 / 6 |
| D | 32666.045818 | +1013.991279 | 815.900 | 1456.314 | 1 | 365/365 | 6 / 6 / 2 |

A/B/D finish the season; C finishes24seconds before final dawn with agent_finished (120 whole nights, all121 reached). No CPU/wall cap or planner errors. B gain comprises14009.232science +25000required +400requests +100reports +31.765uniformity; its missing count falls500→0. C science gains5792.608 and D913.950. A falls22.751.

The result combines exact compute acceleration, fair CPU/wall-clock handling, and genuine Kimi policy controls. It does not isolate Kimi contribution. Six actual model requests per card produced5/4/6/6 accepted reviews and4/2/6/2 policy changes; changed_selections=0 refers to a separate direct-selection counter and does not mean controls had no effect. Formal award eligibility remains organizer-determined.

The first upload failed before agent execution because pip user installation targeted read-only /.local; preserved revisionfc053d28. Replacement installs pinnedNumPy2.2.6 into .vendor with PYTHONPATH=.vendor. Runner publiccheck passed and actual logs show fastpath activated; prepared32files match frozen source except platform image/protocol metadata normalization. Warm checkpoint timings are not a standalone season forecast; the local30CPUbenchguard overrun remains documented.

Leaderboard snapshot 2026-10-04T17:39:45.822539+00:00: rank3, leaderAstroNJU mean30431.893899, gap833.476894. These are current totals, not the earlier CCB benchmark. No final version selected.
