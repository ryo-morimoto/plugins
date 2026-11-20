# Prove: no undefined behavior

Matching output is not enough for `unsafe`. UB often works until the optimizer or compiler version changes, and timings of UB code mean nothing.

## Miri

```sh
cargo +nightly miri test
MIRIFLAGS=-Zmiri-tree-borrows cargo +nightly miri test
MIRIFLAGS=-Zmiri-many-seeds=0..16 cargo +nightly miri test
cargo +nightly miri test --target s390x-unknown-linux-gnu   # big-endian
```

- Finds out-of-bounds, use-after-free, uninitialized reads, misalignment, invalid values, data races; aliasing checks are experimental.
- Checks only the executions you run. Feed it the differential-test generators with a small case count.
- No FFI or networking; slow.
- Emulates many Intel intrinsics from SSE2 to AVX2 and some AVX-512, so SIMD paths can be checked without the hardware.
- Run big-endian after any layout or `transmute` change.

## Sanitizers (real binary, FFI included)

```sh
RUSTFLAGS=-Zsanitizer=address cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu
```

`address` for memory errors, `memory` for uninitialized reads, `thread` for races. Use under fuzzing and integration tests, where Miri is too slow or cannot run.

## cargo-careful

```sh
cargo +nightly careful test
```

Builds std with debug assertions and extra checks: `get_unchecked` bounds, pointer alignment and non-null, `unreachable_unchecked`. Fast and FFI-compatible; catches less than Miri.

## Habits

- State each `unsafe` precondition as `debug_assert!`; run tests and fuzzing with debug assertions on.
- Freeze layout with const asserts on `size_of`, `align_of`, `offset_of!`.
- Snapshot wire/disk bytes for known inputs (golden files, e.g. insta); verify new code reads old data.
- After reordering fields, differential-test derived `Ord` and `Hash`.
