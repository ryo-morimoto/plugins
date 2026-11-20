# TypeScript (derived, not from the source)

1. **Avoid naming**: method chains; arrow functions; destructuring; optional chaining; literals. There is no pipeline operator, so some intermediates need names: keep their right-hand sides simple.
2. **Bindings**: `const` by default, `let`, parameters, exports. Do not repeat in the name what the type states. Types vanish at runtime: validate external data where it enters.
3. **Modules**: ES modules. With `import * as payload`, members drop the prefix (`payload.get`). Methods do not repeat the class name. Do not shadow globals (`name`, `event`, `Map`); alias at the import instead.
4. **Short names**: `x`, `xs`; `i`; `f`; `T`, `K`, `V`; `err`; `_`; `this`.
5. **Compound data**: arrays are plural; maps and records are `valueByKey` (`studentsByClass`). For nesting, name a type alias or order outermost first (`departmentToClassToStudents`). Use labelled tuples or destructuring before coining a type name.
6. **Reads, writes, pure**: reads from outside use `fetch`, `load`, `read`; writes use `save`, `send`, `delete`. Pure functions take no verb (`md5(payload)`, `toBase64`, `lastModified`). **Tension**: `getX` is common for plain accessors, against "`get` implies a read from outside". Default: no `get` on accessors. If the codebase uses `getX` throughout, follow it.
7. **Syntax extensions**: decorators, code generation and type-level utilities are never self-evident: make the name signal that it is special, and document it.
8. **Skimming**: side effects and mutation do not show in syntax; only `await` marks waiting. Default to `const` and `readonly`; keep right-hand sides pure.
