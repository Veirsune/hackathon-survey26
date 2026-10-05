# Official formal evaluation

Mean **30654.85824175**, +114.77590675 against the frozen OFF parent (30540.082335). This is the highest observed mean so far, from one evaluation per configuration.

| Card | Score | Difference from OFF parent | Required missing |
|---|---:|---:|---:|
| A | 23991.891346 | -1.274158 | 1 |
| B | 39969.708011 | +221.985125 | 0 |
| C | 25761.718338 | +231.533104 | 0 |
| D | 32896.115272 | +6.859556 | 2 |

All cards used the available season, with zero model calls and no hard time cap. A/B ended with 15/52 seconds remaining, below the minimum 60-second exposure. Download hashes and official scores were verified.

The change adds bounded short measurements when ordinary planning stalls under low inferred throughput. Measurements retain the existing report criteria and use real returned observations to update beliefs. The retained D log contains 39 measurements, including several nights with three; its report settlement improved by 100, but an additional required miss and lower science gain left only +6.86 net. A/B/C retained logs contain no measurements. These results do not establish a causal or repeatable gain from diagnostic measurements.

The previous OFF result is preserved at tag `formal-feedback-off-mean-30540`; the Kimi branch remains separately available.

Revision: `b0ad4a85-6337-43b6-b6a1-d231f828f576`
Batch: `4d2f3e8d-ac8c-49c1-8fae-ec179fa279b6`
Phase: official online A/B/C/D, 2026-10-05.
