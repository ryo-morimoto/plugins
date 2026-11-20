# Build: lock it first

Profile the build you ship. LTO and codegen-units change inlining, which moves hotspots. These are code-free wins, so take them before editing code.

```toml
[profile.release]
codegen-units = 1
lto = "fat"          # or "thin"; measure both
panic = "abort"      # only if nothing relies on unwinding / catch_unwind

[profile.profiling]
inherits = "release"
debug = "line-tables-only"
```

Profiling runs only, in `.cargo/config.toml`:

```toml
[build]
rustflags = ["-C", "force-frame-pointers=yes", "-C", "symbol-mangling-version=v0"]
```

| Option | Gain | Behavior risk |
| --- | --- | --- |
| LTO | often 10-20%+ | none |
| `panic = "abort"` | small | no unwinding |
| `-C target-cpu=native` | where vectorizable | crashes on older CPUs |
| jemalloc / mimalloc | workload dependent | memory use, addresses |
| PGO | often 10%+ | none; hurts if workload differs |

Change one option at a time and benchmark.

## PGO and BOLT (apply last)

```sh
cargo pgo build && ./target/<triple>/release/app <real workload>
cargo pgo optimize
cargo pgo bolt build --with-pgo      # optional, experimental
cargo pgo bolt optimize --with-pgo
```

- Train on production-like load, not the test suite.
- Put custom rustflags under `[target.<triple>]`; `[build]` flags override PGO's.
- Do not strip symbols before BOLT.
- Applied mid-project, stale profiles blur the effect of each code change.

A build-only change can still expose latent UB: rerun tests optimized, once with ASan.
