# Diagnose: CPU

Classify before reading flame graphs. "Function X is 30%" does not say whether to cut instructions or fix memory access.

## 1. Classify

```sh
perf stat -e cycles,instructions,branch-misses,cache-misses -- ./app
perf stat --topdown -- ./app     # Intel; deeper levels: pmu-tools toplev
```

| Top-down class | Meaning | Fix family |
| --- | --- | --- |
| Retiring | real work | fewer instructions: algorithm, SIMD, bounds checks, inlining |
| Bad speculation | mispredicts | branchless code, lookup tables, sorted data |
| Frontend bound | instruction supply | PGO/BOLT, `#[cold]`, less inlining |
| Backend bound | memory or ports | `diagnose-memory.md`; else split dependency chains, avoid division |

## 2. Locate

```sh
perf record -F 999 --call-graph fp -- ./app
samply record ./app
cargo flamegraph --profile profiling
```

Needs frame pointers and line tables (`build.md`). Inlined callees are charged to the caller: a wide frame means something folded into it is slow.

## 3. Read the code the CPU runs

```sh
cargo asm --lib my_crate::hot_fn --rust   # cargo-show-asm
cargo asm --lib my_crate::hot_fn --mca    # llvm-mca port pressure
```

In the hot loop look for:

- `panic_bounds_check` or `unwrap_failed` branches
- missing ymm/zmm where you expected vectorization (check `--llvm` for why)
- unexpected `call`: memcpy, drop glue, an un-inlined helper
- one serial dependency chain carrying a value across iterations

## Also

- Callgrind: deterministic per-line instruction counts for before/after diffs.
- Coz: causal profiling; estimates the payoff of speeding up a line in threaded code.
