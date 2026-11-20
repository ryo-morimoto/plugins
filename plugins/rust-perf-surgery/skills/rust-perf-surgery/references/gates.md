# Gates: which proof each change needs

Differential testing against the oracle is required for every row. The change type adds the rest. R = required, + = recommended.

| Change | Fuzz | Miri | Sanitizers | Kani / exhaustive | loom | Also |
| --- | --- | --- | --- | --- | --- | --- |
| Build flags only | | | + ASan once | | | rerun tests optimized |
| Safe algorithm / data structure | + | | | | | model-based test, mutants |
| Layout, safe | | | | | | size/offset const asserts, derive-order check |
| Layout with `repr`, `transmute`, FFI | + | R | + | | | big-endian Miri run, golden bytes |
| New `unsafe` | R | R | R ASan | + | | cargo-careful |
| Explicit SIMD | R | R | + | + per-lane kernel | | every feature path vs scalar; lengths 0..=2*lanes+1; unaligned slices |
| Bit tricks, branchless | | | | R | | |
| Float reordering | + | | | | | tolerance contract reviewed first; NaN, +-0, inf, subnormals |
| Locks to atomics, lock-free | | + many seeds | R TSan | | R | shuttle, linearizability check |
| IO path | + | | | | | fault injection, crash consistency |
| Lazy, memoize, reuse, snapshot (`skip.md`) | R sequences | + | + ASan | | | `prove-reuse.md`, negative control |
| Structure swap (`structures.md`) | + | | | | | model-based test, adversarial input |

Where the checks live:

- oracle tests, fuzzing, Kani, mutants: `prove-equivalence.md`
- Miri, sanitizers, cargo-careful, layout: `prove-soundness.md`
- loom, shuttle, TSan: `prove-concurrency.md`
- fault injection, durability: `prove-io.md`
- reuse, laziness, snapshots: `prove-reuse.md`

## CI placement

| When | Run |
| --- | --- |
| Every PR | differential + model tests, Miri on unsafe crates, fuzz corpus replay, iai-callgrind diff, `cargo mutants --in-diff` |
| Nightly | ASan/TSan suites, long fuzzing, `-Zmiri-many-seeds`, big-endian Miri, loom, Kani |
| Pre-release | wall-clock on dedicated hardware, trace replay, fresh PGO profile |
| Post-release | shadow comparison, p99 and error rate |
