# Language packs

Packs add language defaults. They are the only part meant to be extended.

- A pack cannot override `core/`. A conflicting rule is void.
- Precedence: this codebase's own practice, then the pack, then `core/`.
- Only `clojure.md` comes from the source. Other packs are derived and say so in their first line.
- Where a language's habit conflicts with a source rule, record it as a "Tension" with the default and the follow-the-codebase fallback.
- One file per language, at most 2000 characters.

## Sections

| # | Section | Supports |
|---|---|---|
| 1 | Ways to avoid naming | `avoid.md` |
| 2 | Bindings, and what the types already say | `bindings.md` |
| 3 | Modules; shadowing | `functions.md` |
| 4 | Conventional short names | `avoid.md` |
| 5 | Names for compound data | `review.md` row 3 |
| 6 | Reads, writes and pure functions | `functions.md` |
| 7 | Macros and other syntax extensions | |
| 8 | What lets a reader skim | `bindings.md` |

To add a language, copy the headings into `packs/<language>.md` and list it in `SKILL.md`.
