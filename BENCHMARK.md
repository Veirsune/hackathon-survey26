# Official evaluation

Same-version batch `e1d7816c-5857-4fa0-9f8e-d0265b2ff470`, source commit `025b5c1254e36b83a9e1cb46e99c4ed4c818664e`.

**Eight-card sum: 224107.476323. A–D mean: 30562.541178.**

| Card | Score | Required missing | Termination |
|---|---:|---:|---|
| A | 24002.383531 | 1 | survey_complete |
| B | 39911.142914 | 0 | survey_complete |
| C | 25619.463671 | 0 | survey_complete |
| D | 32717.174595 | 2 | survey_complete |
| A1 | 17192.919096 | 38 | survey_complete |
| B1 | 38338.405992 | 0 | survey_complete |
| C1 | 16437.793859 | 0 | survey_complete |
| D1 | 29888.192665 | 16 | global_wallclock_expired |

All eight downloaded scores and CSV hashes were verified. D1 reached the 3600-second wall limit after using only 514.694 normalized CPU seconds. Seven cards completed the season.

Earlier batches had different wall limits and operator-message versions, so cross-batch score differences are not controlled causal effects. This single batch does not establish hidden-card generalization. The platform final-version selection was not changed.

# Local experiment

Frozen public A catalogue, 12-night synthetic terrain scenario, official CPU-clock runner, sequential runs. This is not an official A1 score or a generalization claim.

| Metric | Rules baseline | Kimi station notes |
|---|---:|---:|
| Total | -19031.433906 | -12741.579803 |
| Required missing | 490 | 367 |
| Science score | 5516.319483 | 5653.283175 |
| Model calls | 0 | 1 |

Both completed with no agent errors. One 10.432-second Kimi call extracted the delivered terrain correction; numerical scheduling weights were unchanged. Improvement: 6289.854103. Earlier zero-call test results are retained separately as a test-harness configuration failure.

