# Operate: moves, cheapest risk first

Go down this list only as far as the profile demands. Lower rows help less code and cost more to prove.

| Move | Confirm with | Contract at risk |
| --- | --- | --- |
| Build: LTO, PGO, BOLT (`build.md`) | wall time, frontend bound | none; may expose latent UB |
| Allocation: `with_capacity`, buffer reuse, `SmallVec`, arenas, fewer clones | allocation count | drop timing/order, peak memory, stale bytes in reused buffers |
| Layout: hot/cold split, AoS to SoA, `u32` indices, boxed large enum variants, `align(64)` | L1/LLC misses, `size_of` | derive order (`Ord`, `Hash`, `Debug`), index overflow, FFI and serialized bytes |
| Data structure: faster hasher, sorted `Vec` for map, flat arrays | misses, instructions | iteration order, HashDoS resistance, worst case |
| Algorithm: `sort_unstable`, branchless search, memoize, batch | instructions, mispredicts | stability, tie-breaks, stale caches |
| Safe codegen: iterators, `chunks_exact`, up-front length `assert!`, `#[inline]`, `#[cold]` | asm, instructions | panic site and message, tail elements |
| Unsafe: `get_unchecked`, raw pointers, `MaybeUninit`, `std::arch` SIMD | asm, instructions | memory safety; old panics become UB; untested CPU paths |
| Floats: per-lane sums, `mul_add`, reordering | instructions | bit-exact results |
| Concurrency: atomics for locks, sharding, weaker `Ordering`, lock-free | off-CPU, HITM | data races, linearizability, fairness |
| IO: buffering, batching, `writev`, `pread`, io_uring, grouped fsync | syscalls, p99 | durability, write order, error timing (write vs flush), short writes |

## Rules

- One move per change; re-profile after each. The bottleneck moves.
- Prefer a safe rewrite that lets the compiler drop the check over `unsafe` that skips it.
- Every `unsafe` block gets a `// SAFETY:` comment and a `debug_assert!` of its precondition.
- SIMD: keep the scalar path; it is the oracle and the fallback.
