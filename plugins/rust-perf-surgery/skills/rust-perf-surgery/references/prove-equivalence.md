# Prove: same answers

Strength grows from random, to coverage-guided, to all inputs. Stack as the risk demands.

## Differential test (always)

```rust
proptest! {
    #[test]
    fn fast_matches_reference(v in proptest::collection::vec(any::<u8>(), 0..4096)) {
        prop_assert_eq!(fast::encode(&v), reference::encode(&v));
    }
}
```

Compare `Err` variants and panics (`catch_unwind`) too, not only successes. Bias inputs to edges: empty, 1, around SIMD widths (15, 16, 17, 31, 32, 33), misaligned subslices, max values.

## Model-based (stateful structures)

`proptest-state-machine`: generate operation sequences from a simple reference (`BTreeMap`, `Vec`), apply to the real structure, compare each return value and periodically the full iteration. Call a `check_invariants()` every step. Failures shrink to a minimal sequence.

## Differential fuzzing

```rust
fuzz_target!(|data: &[u8]| {
    assert_eq!(fast::parse(data), reference::parse(data));
});
```

`cargo fuzz run` with ASan finds branches random inputs miss, and out-of-bounds reads that happen to return equal results. Commit the corpus; promote crashes to regression tests.

## No oracle? Metamorphic properties

Round-trip, idempotence, permutation invariance, chunked equals whole.

## All inputs

- Domain of 32 bits or less: loop over every input.
- Larger: Kani proves it bit-precisely.

```rust
#[cfg(kani)]
#[kani::proof]
fn select_matches_reference() {
    let (a, b): (u64, u64) = (kani::any(), kani::any());
    assert_eq!(fast::select(a, b), reference::select(a, b));
}
```

Kani is bounded: extract one loop iteration as a function and prove that; cover the loop with tests and fuzzing.

## Production shadow

For risky changes run old and new behind a flag on sampled traffic, log mismatches with inputs, return the old result. Delete the old path after a clean window; keep the oracle in tests.
