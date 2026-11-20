# Sources

Checked November 2026. Tools move fast: verify flags against current docs.

- Rust Performance Book (profiling, build configuration): https://nnethercote.github.io/perf-book/
- Stabilizer, ASPLOS 2013 (layout bias, 57% link-order effect): https://people.cs.umass.edu/~emery/pubs/stabilizer-asplos13.pdf
- iai-callgrind vs criterion: https://iai-callgrind.github.io/iai-callgrind/latest/html/comparison/criterion.html
- cargo-pgo (PGO, BOLT): https://github.com/Kobzol/cargo-pgo
- perf top-down: https://android-kvm.googlesource.com/linux/+/refs/tags/for-cucl-06-01-22/tools/perf/Documentation/topdown.txt
- pmu-tools (toplev): https://github.com/andikleen/pmu-tools
- cargo-show-asm: https://docs.rs/cargo-show-asm
- Off-CPU flame graphs: https://www.brendangregg.com/FlameGraphs/offcpuflamegraphs.html
- perf c2c walkthrough: https://coffeebeforearch.github.io/2020/03/27/perf-c2c.html
- dhat-rs (heap usage testing): https://docs.rs/dhat
- RFC 3514 float semantics: https://rust-lang.github.io/rfcs/3514-float-semantics.html
- Miri: https://github.com/rust-lang/miri
- Miri intrinsics coverage (2025-12): https://git.ralfj.de/web.git/blob/HEAD:/personal/_posts/2025-12-22-miri.md
- Sanitizers: https://doc.rust-lang.org/unstable-book/compiler-flags/sanitizer.html
- cargo-careful: https://github.com/RalfJung/cargo-careful
- Kani (ASE 2026 paper): https://arxiv.org/abs/2607.01504
- proptest state machines: https://proptest-rs.github.io/proptest/proptest/state-machine.html
- loom: https://docs.rs/crate/loom/latest
- shuttle: https://github.com/awslabs/shuttle
- cargo-mutants: https://mutants.rs
- Order-independent checking by memoized computations (TypeScript PR 65293, source of `prove-reuse.md`): https://github.com/microsoft/TypeScript/pull/65293
- Theory of Constraints, local vs system optimum (`goal.md`): https://medium.com/forte-labs/theory-of-constraints-102-local-optima-3ca8d348f146
- tokio-console: https://github.com/tokio-rs/console
