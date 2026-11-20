# Contract: what must not change

Write this before touching code. Optimizations break the behavior no test ever stated.

## Pin each item with a test or assertion

- Results: return values, error variants, which inputs panic.
- Order: iteration order, sort stability, tie-breaking.
- Floats: bit-exact, or a tolerance in ulps? Rust never reassociates or fuses to FMA by itself (RFC 3514); only NaN sign/payload is nondeterministic. So build flags must not change float results, but your own reordering or `mul_add` will. Moving from bit-exact to tolerance is a spec change: review it separately, first.
- Side effects: syscall order, fsync-before-ack, log output.
- Concurrency: linearizability, fairness, cancel safety.
- Resources: peak memory, fds, stack depth.
- History: results that depend on what ran or was cached before (order of work, limits, budgets). State the equation: "every answer equals the answer computed from scratch, in the same mode".
- Layout: size, align, offsets, wire/disk bytes. Derived `Ord`, `Hash`, `Debug` follow field order.

## Oracle

Keep the old implementation in a `reference` module (`#[cfg(test)]` or a feature). Slow and obviously correct is ideal. If it has bugs, decide explicitly whether they are part of the contract.

## Are the tests strong enough?

```sh
cargo mutants -f src/hot_path.rs
```

A missed mutant is a change your tests cannot see (or an equivalent mutant). Add tests until every miss is explained. Do this before optimizing.

## Hypothesis

One sentence: "counter X drops N% because Y". If the result disagrees, do not merge until you know why.
