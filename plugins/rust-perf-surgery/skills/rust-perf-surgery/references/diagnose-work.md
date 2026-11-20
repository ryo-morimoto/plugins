# Diagnose: is the work needed?

A profile says where time goes, not whether the work had to happen. Count before choosing a move. Use counters behind a feature flag; do not infer counts from a profile.

## First: time per unit

Rank time by top-level unit (request, file, statement, batch). One outlier beats a flat profile: read the outlier's call tree first.

## Then count

| Question | Count | Points to |
| --- | --- | --- |
| How much of what is built is ever read? | built vs read | lazy construction, narrow query |
| Does the same computation repeat? | calls per distinct input | memoize |
| Who reads the heaviest result, and how much of it? | readers, share read | narrow query |
| How much work is redone per unit of change? | work replayed after a small edit | reuse, differential update |
| Are the queries known ahead? | queries per batch | batch or offline |
| What is the real input? | size vs L1/L2/L3/RAM, skew, duplicates, sorted runs | `structures.md` |

## Reading the result

- Low used share or a narrow reader: `skip.md`.
- Work is needed and concentrated: `moves.md`.
- Wrong structure for the input: `structures.md`.
- Flat profile, every count healthy: speed moves are exhausted. Reuse the result (`skip.md`) or stop (`goal.md`).

## Rules

- Report each count with the command that produced it.
- Mark any number that was inferred, not counted.
- Take inputs from real data. Uniform random input hides skew, sorted runs and duplicates.
- Check for an existing switch or upstream change that already removes the work before writing one.
