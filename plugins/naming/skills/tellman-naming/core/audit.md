# Auditing names across a scope

Use when asked to rename, delete or merge names in files, a module or a branch. The goal is a fixpoint: one more full pass by these rules finds nothing. Reach it within one call; do not leave it to the user to ask again.

1. **Fix the request.** Scope (paths). Apply or report: a request to change names means apply. Judge by these rules alone unless the user asks to match the codebase's practice. Names not yet released (unmerged branch, draft) count as internal.
2. **Read every file in `core/`**, and the pack for each language in scope. Skipping one changes verdicts.
3. **Read the decision file** (`decisions.md`) if the repository has one; keep it out of the inventory.
4. **Inventory mechanically:** run the skill's `scripts/inventory.py <paths>`, plus `--collisions` and `--unused`. Every surface counts: identifiers, files and modules, commands and flags, data and config keys, CSS classes and custom properties, HTML ids, terms in docs. Reading alone misses surfaces.
5. **Judge every entry** with `review.md`: delete, merge, rename or keep. Collisions are row 2 candidates; unused names are row 0.
6. **Apply.** Then run `inventory.py <paths> --words <each old word>` and repeat steps 4–5 on the result: your own renames leave remnants and create collisions. Stop when a pass finds nothing. Report how many passes it took.
7. **Record** every change and every deliberate keep in the decision file.
8. **Second look:** a fresh agent, given only the result and this skill, reviews for misses. It reports findings; it does not choose new words. Accepted findings go through steps 5–7. Skip only if the user says so: your own last pass is not independent.

Several words usually fit a finding, so two audits pick different ones. That is expected; the decision file keeps them from undoing each other.
