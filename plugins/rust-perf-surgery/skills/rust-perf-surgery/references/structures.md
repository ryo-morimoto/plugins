# Operate: choose the structure

Memory access shape, input distribution and who can craft the worst case decide performance; asymptotics rarely do. The first candidate is the first thing to measure.

| Situation | First candidate | Pitfall |
| --- | --- | --- |
| General map | `hashbrown` / std `HashMap` | untrusted keys need a keyed hash; pre-size against resize spikes |
| Lookup, fixed key set | minimal perfect hash + array | absent keys map somewhere; keep a key check |
| Membership, fixed set | binary fuse or ribbon filter | needs all keys at build time |
| Membership, growing set | blocked Bloom; cuckoo if deletes | less compact than static filters |
| Sorted data, no updates | Eytzinger or S+ tree, batched queries | gains throughput, not single-query latency |
| Ordered index, concurrent updates | B-tree + optimistic lock coupling | lock-free trees, learned indexes usually lose |
| Sort | std; radix or SIMD sort for big fixed-width keys | comparator must be a strict weak order |
| Cache eviction | SIEVE or S3-FIFO | evidence is web traces; replay your own |
| Shortest path | Dijkstra; buckets for integer weights | skip the 2025 theory result |
| Sequence similarity | bit-parallel, bounded distance, pre-filter | no exact subquadratic algorithm exists |
| Aggregates with updates | offline if queries are known ahead | fully dynamic structures are heavy |
| Search over states | one state, differential update | state copies bound the rate |

## Rules

- New paper: which cost model, how many log factors, does its worst case occur in your input, can one technique be lifted out? Usually only the last ships.
- A known lower bound is a signal to stop seeking a faster exact algorithm. Spend on output-sensitive bounds, bit-parallel or SIMD constants, or filter-then-verify.
- Prefer the plain structure until a measurement on your input says otherwise.
- A microbenchmark gain is not the application's gain. Report both.
