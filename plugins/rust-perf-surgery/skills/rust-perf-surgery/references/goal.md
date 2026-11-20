# Goal: the system metric and its constraint

Local speedups do not add up. A gain away from the constraint is zero for the system, and it still costs complexity, memory and proof.

## Before any change

- System metric: what the user feels (end-to-end latency, throughput, peak RSS), measured on the real path. Write the target.
- Budget: split the metric into stages that sum to it. The unexplained remainder is a stage too.
- Constraint: the stage with the largest share. Work only there.
- Ceiling: if this stage cost nothing, what would the metric be? If that misses the target, change the plan, not the code.

## While working

- Proxies: instruction counts, microbenchmarks and hit rates stand in for the metric. A proxy that improves while the metric does not is a failed change.
- Subordinate: accept a slower part (tracking, laziness, an extra pass) when the metric improves. Record what got slower.
- After each win, redo the budget. The constraint moves.

## Stop when

- the target is met;
- the ceiling shows it cannot be met under the contract (report that, with the numbers);
- the next constraint is outside the code you own.

## Local move or system change

| | Local move | System change |
| --- | --- | --- |
| Gives | fast feedback, small diff, easy proof | removes whole stages |
| Costs | capped by the stage's share; complexity piles up | whole-path measurement, wide diff, harder proof |
| Use when | the stage is the constraint and the move fits | the ceiling of local moves misses the target |

## Signs that local optimization has spread

- Many merged wins, flat system metric.
- More `unsafe`, special cases and caches nobody owns.
- Benchmarks that no longer resemble the real path.
- Parts tuned for different inputs, or for one session's workload.
- Fixes for one case that make the general path slower or harder to prove.

If two or more appear, stop adding moves and redo the budget.
