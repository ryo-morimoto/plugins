# Clojure (from the source)

1. **Avoid naming**: threading (`->`, `->>`); anonymous functions; literal values.
2. **Bindings**: vars, parameters, `let`. No static types: check invariants where data enters the system.
3. **Modules**: a namespace holds one datatype or one outside resource; members drop the shared word (`payload/get`). To shadow a core function, exclude it at the top of the namespace and define yours at the bottom, so accidental use fails to compile. Do not shadow core names with parameters (`m`, `k`, not `map`, `key`).
4. **Short names**: `x` any value; `xs` sequence; `m` map; `f` function; `ms`, `fs`; `this`; `[a b c & rst]` same-typed arguments; `form` expression; `body` variadic macro forms.
5. **Compound data**: a map of known shape takes the entry's name (`student`); sequences are plural; maps are `key->value`, nested `department->class->students`; tuples are `a+b`. Plurals of these are ambiguous (`tutor+students`): if context cannot settle it, coin a documented term (`tutelage`).
6. **Reads, writes, pure**: a verb when reading from or writing to outside (`get-payload`, `delete-payload`, `compress-and-get-payload`). Outside core, `get` implies a read from outside. Pure functions take no verb (`md5`, `timestamp`, `->base64`); add context in broad namespaces (`payload-md5`). `!` is not universal; do not rely on it.
7. **Macros**: the name should signal a macro and prompt reading it. `with-` names and names built on `def` or `let` need predictable expansions. A macro used in one namespace need only not mislead.
8. **Skimming**: a `let` right-hand side can be skipped if free of side effects. Make effects stand out consistently (explicit `do`, blank lines, or binding to `_`).
