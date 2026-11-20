# Evidence: native or custom UI

Situation type T4: a desktop app with native UI per OS. Single source so far: one project, one traced case (a custom tab bar, 2024 to 2026). Treat this skill as a hypothesis.

## The case

Native tabs blocked several things at once:

1. Inconsistent product. Tabs could not work in the app's own floating window or in non-native fullscreen, because the OS tabs need a titlebar.
2. Many requests, one limit. At least six separate requests (size, position, direction, color, placement) hit the same native limit.
3. Workaround debt. A tweak to the native titlebar broke after an OS update. The team stopped adding options to it.

What did not tip it: one popular request with many votes and a ready pull request, and personal taste.

After deciding to go custom, the stated target was "looks and feels 90% native". Two years later it had not shipped.

## Five situations seen

| Situation | Response |
| --- | --- |
| Native part exists | Use it |
| Platform has no such idea | Build it, follow platform habits |
| Exists but gets in the way | Replace it |
| Exists, lacks one thing | Small opt-in tweak |
| Exists, limits pile up | Plan a custom part |

## Test result and open question

In a with/without test on a file-picker scenario, this skill changed the answer 3 of 3 times (build a custom picker). Without it, the model kept the OS picker and built a separate project browser. Which is better is not settled. Check first whether a different component can route around the limit.

## Limits

- One case, read from excerpts, not full threads.
- Present as a pattern from public records, never as anyone's words.
