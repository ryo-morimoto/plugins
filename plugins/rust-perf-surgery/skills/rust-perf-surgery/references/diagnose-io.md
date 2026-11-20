# Diagnose: IO and waiting

Waiting is invisible in CPU profiles. Measure off-CPU time with the stacks that blocked.

## 1. On-CPU or off-CPU?

If `perf stat` task-clock is far below wall time, the program mostly waits: IO, locks, or the run queue.

## 2. Off-CPU flame graph (bcc)

```sh
offcputime -df -p $(pgrep -nx app) 30 > out.stacks
flamegraph.pl --color=io --countname=us < out.stacks > offcpu.svg
```

- Width = total blocked time on that path. Idle pools dominate; filter to request frames.
- It shows where a thread blocked, not why. `wakeuptime` / `offwaketime` add the waker's stack (lock holder, writer).
- Needs frame pointers. Scheduler events can reach millions per second: check the rate first.

## 3. Syscalls and devices

| Question | Tool | Look at |
| --- | --- | --- |
| Which syscalls, how often | `strace -c -f`, `perf trace -s` | calls per request, bytes per call |
| Block device latency | `biolatency`, `biosnoop` | the tail, not the mean |
| Page cache | `cachestat` | hit ratio |
| fsync cost | `strace -T -e trace=fsync,fdatasync` | count and duration |

strace slows the target heavily: use it for counts, eBPF tools for timing.

## 4. Async runtimes

OS stacks do not show task waits. tokio-console (needs `console-subscriber` and `--cfg tokio_unstable`) shows per-task poll counts and busy / scheduled / idle time.

- Long busy polls: blocking call or heavy compute inside async; move to `spawn_blocking`.
- Long scheduled: workers starved or hogged.
- Long idle: external IO; go back to steps 2-3.
