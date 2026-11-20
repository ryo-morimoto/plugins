# Prove: concurrency

Stress loops rarely hit the bad interleaving and cannot replay it. Control the scheduler instead.

## loom: exhaustive, small models

```rust
#[cfg(loom)]
#[test]
fn counter_is_exact() {
    loom::model(|| {
        let n = loom::sync::Arc::new(loom::sync::atomic::AtomicUsize::new(0));
        // spawn 2 loom threads, mutate, join, assert
    });
}
```

```sh
RUSTFLAGS="--cfg loom" cargo test --release --test loom_counter
```

- Swap `std::sync` / `std::thread` for loom types behind `cfg(loom)`.
- Permutes executions under the C11 memory model, so it also tests relaxed `Ordering` choices.
- Limits: `SeqCst` is treated as `AcqRel` (false alarms); some load-buffering executions are not explored (misses possible). Keep to 2-3 threads and a few operations.

## shuttle: randomized, larger scenarios

`shuttle::check_random(|| ..., iterations)` or `check_pct`. Not sound, but scales far beyond loom and replays a failing schedule deterministically. Use for whole-component tests.

## Real binaries

- ThreadSanitizer on integration tests: `-Zsanitizer=thread` (see `prove-soundness.md`).
- Miri detects data races; vary interleavings with `-Zmiri-many-seeds`.

## Specification level

- Record concurrent operation histories and check a sequential model can explain them (linearizability).
- Assert invariants at quiescent points: counts conserved, no lost or duplicated items.
- State fairness and cancel-safety expectations as tests if callers rely on them.

## After the fix

Re-run `perf c2c`: removing a lock often creates false sharing on the new atomics.
