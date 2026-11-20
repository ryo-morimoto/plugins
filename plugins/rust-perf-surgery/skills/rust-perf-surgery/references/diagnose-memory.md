# Diagnose: memory

Three different problems, three different tools: too many allocations, poor cache use, cache lines fought over by cores.

## Allocations

| Tool | Shows | Limits |
| --- | --- | --- |
| DHAT (Valgrind) | hot allocation sites, peak, hot memcpy | slow; Linux-like only |
| dhat-rs | same idea on any platform | needs small code change |
| heaptrack, bytehound | heap over time, call stacks | Linux |

Read in this order: count, bytes, lifetime. Short-lived, frequent allocations vanish with buffer reuse or stack storage.

## Cache misses

```sh
perf stat -e L1-dcache-load-misses,LLC-load-misses,dTLB-load-misses -- ./app
perf record -e cache-misses:pp --call-graph fp -- ./app
perf mem record -- ./app && perf mem report
```

Trace the missing load back to a struct field. Pointer chasing (`Box` trees, linked lists, `HashMap<K, Box<V>>`) hurts more than its miss count: each miss blocks the next load. Cachegrind is deterministic but does not model the prefetcher.

## Layout

```sh
RUSTFLAGS=-Zprint-type-sizes cargo +nightly build --release
```

Then freeze what you tuned so unrelated edits cannot regress it:

```rust
const _: () = assert!(std::mem::size_of::<Node>() == 64);
const _: () = assert!(std::mem::offset_of!(Node, hot_key) == 0);
```

## False sharing

```sh
perf c2c record -g -- ./app
perf c2c report --stdio
```

HITM = a load that hit a line modified in another core's cache. A line with high HITM written at different offsets by different threads is false sharing. Fix: `#[repr(align(64))]` or `crossbeam_utils::CachePadded` per-thread data.
