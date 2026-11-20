# Prove: IO and side effects

Batching and buffering legitimately change the syscall sequence, so do not compare sequences. Compare outcomes and guarantees.

## Make IO observable

Put IO behind a trait. In tests, a recording fake logs every call: kind, offset, length, and where each fsync falls.

## What must match between old and new

- Final bytes on disk or on the wire for the same inputs.
- Durability: at the moment a caller receives an acknowledgement, the data it covers has been fsynced.
- Ordering that readers can observe.
- Error reporting: same error kind surfaced to the same caller. Buffering moves errors from `write` to `flush`; make sure nothing drops them (check `Drop` paths, `BufWriter::into_inner`).

## Fault injection

Run old and new against a fake that injects:

- short writes and short reads
- `EINTR`, `EAGAIN`
- `ENOSPC` and mid-stream failures
- failure on fsync

Both must leave equivalent state and report equivalent errors.

## Crash consistency

From the recorded write log, replay every prefix as a "power loss" (optionally dropping un-fsynced writes), run recovery, and check the contract: no acknowledged data lost, no corruption, no partial record visible.

## Async and timing

- Test with a paused clock (`tokio::time::pause`) so timeouts and batching windows are deterministic.
- Check cancellation at each await point: dropping the future must not lose or duplicate buffered data.

## Performance evidence

Report syscalls per request, bytes per syscall, fsync count, and p99 latency, not only throughput. A batching win that hurts tail latency is a regression for interactive callers.
