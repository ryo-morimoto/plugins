# Prove: reuse gives the from-scratch answer

For every move in `skip.md`. "0 mismatches" is evidence; say how many cases, and what was not covered.

## 1. Build the counterexample generator first

- Random sequences of edits, orders or queries; compare with a fresh run, order included.
- Add adversarial cases aimed at the reuse boundary.
- Negative control: break the reuse on purpose (skip an invalidation, corrupt a key) and confirm the generator catches it. A generator that never fails proves nothing.

## 2. List how earlier state reaches a result

Put one rule on each path, enforced by a type or a test.

| Path | Rule |
| --- | --- |
| Reads of cached values | record them as dependencies, or bar the read |
| Side effects (diagnostics, marks) | record with the result; replay once on reuse |
| Computations in progress (cycles) | discard what was computed inside; recompute |
| Limits (depth, count, budget) | see step 4 |
| State of one request | keep nothing it cached |

## 3. Judge by one question

Would computing this from scratch give the same result? Keep it if yes; otherwise discard and recompute. Enter cycles from a canonical member, such as the one declared first.

## 4. Limits

- Look for a monotonic argument: caching only shortens the stack, so a limit above the from-scratch maximum does not depend on order.
- If none exists, store with the result how much it consumed (height, charged cost), so a reuse can tell whether recomputing there would give up.

## 5. Cost of tracking

Measure where tracking cost concentrates. Drop it only where you can argue the equation still holds.

## 6. Real projects

Judge each difference one by one, by whether the new answer is right, not by whether it matches the old. Pin each with a test.

## Also run

Miri or ASan when reuse keeps pointers into old memory; a long session for leaks and leftover processes.
