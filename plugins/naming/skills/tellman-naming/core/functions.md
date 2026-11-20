# Functions and modules

"Outside" means anything beyond the data the current thread already holds: disk, network, another process, a queue, shared mutable state.

| The function | Name |
|---|---|
| Reads from outside (query, I/O read) | Include a verb; describe what is returned (`fetch-payload`) |
| Is a pure function | No verb where possible (`md5`, `timestamp`, `->base64`) |
| Writes to outside (command, side effect) | Include a verb; describe the effect (`delete-payload`) |

- Reading shared mutable state does not count as reading from outside; writing it counts as a write.
- A function that both reads and writes names both (`compress-and-get-payload`) and documents the behaviour.
- A pure function that builds a changed structure often needs a verb. If the bare name is ambiguous but the call site is clear, that is enough.
- Do not rely on a marker for side effects (`!` and the like). Avoid impure functions where you can; document them where you cannot.

## Modules and namespaces

- A module should hold functions that share a datatype, or share the same outside resource, or both. It then narrows its members, and they drop the shared word (`payload/get`, not `payload/get-payload`).
