# Definitions, parameters and locals

| Binding | You control | The name hides |
|---|---|---|
| Top-level definition of immutable data | The name and the value | The value |
| Function parameter | The name only; callers choose the value | The callers' code |
| Local binding | The name and the right-hand expression | The right-hand expression |

- **Parameter:** name it for what the function needs from it, not for what today's callers pass.
- **Local, name is self-evident:** the reader may skip the right-hand side. This holds only if the right-hand side has no side effects.
- **Local, name is not self-evident:** keep the right-hand side as simple as possible, because the reader must read both.
- **Side effects must stand out.** Give an effectful expression its own statement or line; do not bury it in a binding the reader will skip.
- **Use the narrowest accessor** the code needs (`keys` rather than a full traversal). Code that reads narrowly supports a narrow name.
- **Repeated value:** a short name may beat a self-explaining one.
