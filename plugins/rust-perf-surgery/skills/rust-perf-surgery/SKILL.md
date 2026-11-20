---
name: rust-perf-surgery
description: Rust performance work (CPU, memory, IO, caching, reuse, data-structure choice) that moves the system metric and proves behavior stays identical. Use for any Rust speedup, profiling or benchmarking.
---
# Rust perf surgery

A speedup that changes behavior is a bug. One that leaves the system metric flat is waste. Old code is the oracle. One hypothesis per change. Measure, never estimate.

Read from `references/` only what a step needs.

1. Goal: system metric and its constraint. `goal.md`
2. Contract: what must not change. `contract.md`
3. Baseline: `build.md`, `baseline.md`
4. Diagnose: where time goes (`diagnose-cpu.md`, `diagnose-memory.md`, `diagnose-io.md`); is the work needed (`diagnose-work.md`)
5. Operate: faster `moves.md`; less work `skip.md`; other structure `structures.md`
6. Prove: `gates.md` picks from `prove-*.md`
7. Confirm on the system metric; fill `report.md`

Revert wins that don't reproduce. Citations: `sources.md`.
