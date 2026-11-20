# Recorded naming decisions

The rules say why a name is wrong; they rarely pick one replacement. Without a record, each later pass renames again to a word it likes better. Keep one file per repository, `naming-decisions.md` at the root, unless the user names another place. Leave it out of the inventory.

One row per name, oldest first:

| name | verdict | now | reason | date |
|---|---|---|---|---|
| `fetchUser` | rename | `fetch-user` | pack: kebab case | 2026-01-05 |
| `cache` | keep | | rows 1, 2, 4 checked: one cache, read where it is named | 2026-01-05 |

- Look a name up before judging it. A recorded verdict stands unless you find a row or rule its reason did not consider. Then add a new row citing it; do not edit old rows.
- A keep binds only if its reason names the rows checked. Never record keeps in groups ("all config keys"); a grouped keep hides names nobody judged.
- Preferring another word is not a new reason (`review.md`: keep is a real answer).
- Remove a row when the name in `now` (or, for keeps and deletes, in `name`) exists nowhere; version control keeps the history.
