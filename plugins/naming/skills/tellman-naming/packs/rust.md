# Rust (derived, not from the source)

1. **Avoid naming**: iterator chains; closures; `?`; literals; rebinding the same name (`let line = line.trim();`) instead of coining one per stage.
2. **Bindings**: `const`, `static`, parameters, `let`. Newtypes and enums put much of the meaning in the type: do not repeat it in the name. Construct through validation (`TryFrom`) where data enters.
3. **Modules**: paths give context, so members do not repeat the module name (`payload::get`). A module-local `Result` is accepted but asks more of the reader: document it.
4. **Short names**: `self`; `T`, `U`; `K`, `V`; `E`; `f`; `i`, `n`; `buf`; `e`, `err`; `other`, `rhs`; `_`.
5. **Compound data**: collections are plural; maps are `value_by_key` (`students_by_class`). Give nested shapes a type alias or struct. Destructure tuples; define a struct only when ambiguity remains.
6. **Reads, writes, pure**: reads from outside use `fetch_`, `read_`, `load_`; writes use `write_`, `send_`, `delete_`. Pure functions take no verb; conversions use `as_` (cheap borrow), `to_` (costly), `into_` (consuming). No `get_` on accessors. `&mut`, `async`, `unsafe` and `Result` show in signatures: do not restate them in the name.
7. **Macros**: `!` at the call site already signals a macro. The expansion is still not self-evident: document it, and keep derive and attribute expansions predictable.
8. **Skimming**: bindings are immutable by default; `mut` and `&mut` mark change. I/O does not show in types: give an effectful expression its own statement.
