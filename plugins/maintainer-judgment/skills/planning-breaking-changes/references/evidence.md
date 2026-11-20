# Evidence: planning breaking changes

Read this when the user asks "why" or doubts a step.

## Situation types

- T1: a library API with a compatibility promise. You cannot reach the callers' code.
- T2: CLI flags, config keys and defaults. You cannot edit users' files, but you can add aliases or a way back.
- T6: a framework that ships defaults to new apps. Old apps keep working.

## Confirmed (two or more projects)

| Pattern | Support | Counter | Projects |
| --- | --- | --- | --- |
| Decide who pays the moving cost before you break it | 10 | 1 | curl, Ghostty, Rails |
| Keep public names; make old calls harmless (ignore, alias) | 10 | 1 | curl, Ghostty |
| Changing a setting or default: leave a way back, keep old users working | 23 | 4 | curl, Ghostty, Rails |

## Not confirmed yet

- Gather usage evidence, ask in public, set a date, go in stages. Strong in one project only.
- In T1, proposals that change an existing guarantee stop; adding forms pass. Predicted 24 of 26 (a naive guess got 22), but one project only.
- Notice length follows evidence of users: with users, wait; with none and no way to vouch for quality, short or no notice. Predicted 10 of 11 removals in advance (a naive guess got 7), but long notices for nearly unused items still happen.
- Most changes that keep a compatible path (stub, alias, a setting to go back) shipped with no advance notice. Notice was mostly kept for removals that force users to switch backend, protocol or platform. Not tested yet.
- Long broken with no reports is read as "no users"; notice is shortened or skipped.

## Who pays: three ways seen

- Nobody: wait, keep the name.
- You, by hand: fix the callers yourself.
- You, by machine: aliases, a setting to go back, "unsupported" instead of a crash.

## Limits

- Evidence was picked from blogs, release notes and PRs. Not a random sample.
- One reviewer judged support and counterexamples.
- Present as patterns from public records, never as anyone's words.
