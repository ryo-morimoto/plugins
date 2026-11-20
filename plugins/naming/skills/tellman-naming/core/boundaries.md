# Layers, interfaces and conventions

- **Readers differ by depth.** Deep internal code has few, determined readers. Top-level and exported code is read by newcomers and experts alike. A code name or terse term that suits a three-person internal module does not suit a public surface, and the reverse.
- **A layer whose two sides share one purpose** costs the reader a context switch and returns nothing. Consider removing it.
- **A boundary with a single user does not hold.** The two sides grow together and the boundary's name starts to mislead. Do not add an interface, version or abstraction for one caller.
- **Exported interfaces become hard to change;** mistakes can outlive their authors. Let a foundational interface mature inside your own code first. Export it only after that.
- **Conventions are a tool, not a solution.** If something can enforce the assumption (a type, a constructor, a wrapping layer), prefer that to a naming convention. Use a convention when enforcement costs too much. Do not take comfort from merely having one.
- **When an assumption behind a name proves false,** pick one: widen the model, wrap it in a layer, adopt a convention, or narrow the intended use. Say which.

Precedence when choosing a form: this codebase's own practice when the user asks to follow it (see `survey.md`), then the language pack, then the defaults here.
