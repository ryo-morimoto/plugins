# Evidence: choosing defaults

Situation types: T2 (config and defaults users touch) and T4 (desktop apps with native UI). Read this when the user asks "why".

## Confirmed (two projects)

| Pattern | Support | Counter | Projects |
| --- | --- | --- | --- |
| Start from an outside standard (OS, prior apps, specs); user evidence can override it | 12 | 1 | Ghostty, Rails |
| Changing a default: leave a way back, keep old users working | 23 | 4 | curl, Ghostty, Rails |

## Single source (one project)

- Dangerous things stay off by default, even if handy.
- Count "most people" per group (OS, keyboard layout), not overall.
- No proof, no change. If a small group's basic input breaks, split the default by group.
- An unused feature should cost nothing.
- The six-step order in SKILL.md was built from a handful of cases and is not tested.

## Test result

In a with/without test, this skill made no difference on two scenarios: a model without it reached the same answers. Its value is the checklist, not new conclusions. One gap neither version covered: saying in advance what evidence would justify changing the default later.

## Limits

- Evidence was found by keyword search.
- How much proof is enough is unknown.
- Present as patterns from public records, never as anyone's words.
