# Find the codebase's own practice

"Match the existing code" only works if you look. Do this before judging or choosing a name.

1. **Classify what is named:** map or dictionary; sequence; pair or tuple; boolean or predicate; conversion; function that reads from outside; function that writes; constructor; type; module; parameter of a public function.
2. **Collect at least ten existing names of the same kind,** nearest first: same file, same module, then the whole repository. List definitions with a search, for example:
   - Clojure: `grep -rhoE "\((def|defn|defn-|defmacro) [^ ]+" src`
   - TypeScript: `grep -rhoE "(const|let|function|type|interface|class) [A-Za-z0-9_$]+" src`
   - Rust: `grep -rhoE "(fn|struct|enum|trait|const|static|let) [A-Za-z0-9_]+" src`
   Then filter to the kind (maps: names bound to a map constructor or literal; predicates: names ending `?` or starting `is`/`has`; and so on).
3. **Tally the forms.** Example: maps: 14 `key->value`, 2 bare nouns, 1 `-map` suffix.
4. **Decide the local default.**
   - One form in about two thirds or more: that is the default here, even if the pack says otherwise.
   - No clear majority: there is no local default. Use the pack.
   - Fewer than five examples: say the sample is too small and use the pack.
5. **State the tally in one line** with your verdict, so the reader can check it.

Also search every use of the name under review before judging it: a name is read at its uses, not at its definition.
