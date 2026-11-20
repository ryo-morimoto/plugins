# Baseline: benchmarks you can trust

Measurement bias can exceed your gain: changing link order alone moved performance by up to 57% (Stabilizer, ASPLOS'13).

## Three layers

| Layer | Tool | Role | Weakness |
| --- | --- | --- | --- |
| Deterministic | iai-callgrind | CI gate; resolves ~0.1% in instruction counts | only correlates with time |
| Wall-clock | criterion, divan | final judge on a quiet bare-metal box | too noisy on cloud CI |
| Macro | production trace replay | throughput, p50/p99/p99.9 | slow, no attribution |

Fewer instructions with more cache or branch misses is a loss. Use both of the first two. A microbenchmark gain is not the application's gain: the macro layer decides.

## Quiet the machine

- Governor `performance`, turbo off.
- `isolcpus` + `taskset`; leave the SMT sibling idle.
- Interleave runs A B A B to cancel thermal drift.

## Inputs

- Wrap inputs and results in `std::hint::black_box`.
- Sizes that fit L1, fit L2, exceed LLC.
- Sorted, random, adversarial distributions; real data for the final call.
- Mean and tail: resizes and compactions show in the tail.

## Accept a win under 5% only if

1. The predicted counter moved in the predicted direction.
2. It survives an unrelated relink: reorder functions, pad the environment, swap the allocator.
3. It has the same sign on a second microarchitecture.

## Allocation budgets as tests

dhat-rs heap testing fails a test when counts drift:

```rust
#[global_allocator]
static ALLOC: dhat::Alloc = dhat::Alloc;

let _p = dhat::Profiler::builder().testing().build();
run_workload();
dhat::assert_eq!(dhat::HeapStats::get().total_blocks, 96);
```

One such test per integration-test file; they interfere otherwise.
