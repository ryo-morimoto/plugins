# Terms for explaining a verdict

| Term | Meaning | Example |
|---|---|---|
| Sign | The text of the name | `id` |
| Referent | What it currently points to | a UUID |
| Sense | The properties the name promises, now and later | uniqueness |

- **Count only what stays true.** A fact true only of today's implementation ("ids are 128 bits") is not part of the sense. Treat it as false, or the implementation becomes permanent.
- **Narrow.** A good name rules out what it cannot stand for. Narrow is not the same as specific: a name that states storage, type or algorithm is specific, and it exposes what should stay free to change.
- **Two names for one value** are right when you expect the two to diverge: same referent, different senses.
- **Some mismatch is normal.** An `id` promises uniqueness; UUIDs are only very likely unique. When every option is inconsistent somewhere, choose which mismatch to accept and say so.
- **Narrow versus consistent:** decide by who reads the code.

## Everyday words and coined terms

| | Everyday word (`student`, `id`) | Coined term (`monad`, an invented compound) |
|---|---|---|
| Readers | Understand at once, each in their own way | Must learn it, then agree exactly |
| Use when | Readers are new or mixed | Readers will have read the documentation |

- Names for compound data structures are usually coined terms. Use them only where readers will have read the documentation.
- When the readership changes, choose again.
