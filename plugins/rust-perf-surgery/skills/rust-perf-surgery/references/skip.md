# Operate: do less work

Use after `diagnose-work.md` shows work that is unused, repeated or redone. Cheapest proof first. Every row needs `prove-reuse.md`.

| Move | Confirm with | Contract at risk |
| --- | --- | --- |
| Lazy construction: build on first request | results built | evaluation order, when errors appear, anything that depends on how much was cached |
| Narrow query: answer one lookup without building the whole | full builds | must equal the full answer, order included |
| Memoize within a run | hit count | results that depend on the caller's stack or on a limit |
| Reuse across runs or edits | work replayed | results that depend on what was cached when they were computed |
| Batch or offline: reorder when all queries are known | passes over data | per-item latency, output order |
| Differential update: one state, advance and undo | state copies | the inverse must be exact; floats drift |
| Snapshot and resume | work replayed | later work reads earlier state; copy-on-write faults cost time |

## Rules

- State the equation first: "every answer equals the answer computed from scratch, in the same mode".
- Reuse the largest unit whose inputs you can name. If you cannot list what a result read, you cannot reuse it.
- When a result is unsafe to reuse, exclude that result, not everything near it. Measure how much each exclusion rule gives up.
- A resumed or lazy path can be slower than the fresh one. Measure both and keep a policy that picks the faster.
- Prefer a mode the upstream project already tests over a private one.
- A mode that changes observable output near a limit is a contract change: name it, and make the fresh run in that mode the oracle.
