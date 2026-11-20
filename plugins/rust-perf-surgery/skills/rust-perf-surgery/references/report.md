# Confirm and report

One change, one hypothesis, two kinds of evidence. Use this template for the PR or summary.

```markdown
## Goal
System metric, target, and the stage that is the constraint (goal.md).

## Hypothesis
<counter> drops <N>% because <mechanism>.

## Bottleneck evidence (before)
Top-down class / miss counts / off-CPU share, with the command used.

## Change
Move applied (from moves.md) and why it is the smallest that fits.

## Contract touched
Items from contract.md this change could affect, and the test pinning each.

## Equivalence evidence
- Differential test: <cases>, oracle = <reference>
- Gates required by gates.md: <list>, each with result
- Mutants on changed lines: <caught>/<total>, misses explained

## Performance evidence
| Metric | Before | After | Delta |
| System metric (real path) | | | |
| Instructions (iai-callgrind) | | | |
| Target counter (misses, allocs, syscalls) | | | |
| Wall-clock, machine A | | | |
| Wall-clock, machine B | | | |
| p99 (if latency-sensitive) | | | |

## Did the prediction hold?
Yes / no. If no: explanation, or the change is withdrawn.

## Not done / rejected attempts
What was tried and did not help, so nobody repeats it.

## Not verified
Every check not run on the final code; which numbers were inferred, not counted.
```

## Before calling it done

- The system metric moved, and the predicted counter with it.
- A win under 5% passed the three checks in `baseline.md`.
- The oracle stays in the test suite.
- Every `unsafe` block has a `// SAFETY:` comment and a `debug_assert!`.
- New benchmarks and fuzz corpus are committed, so the gain is guarded.

Report failures plainly. A measured "no improvement, reverted" is a valid result.
