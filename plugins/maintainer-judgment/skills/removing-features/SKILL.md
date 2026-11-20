---
name: removing-features
description: Checks a plan to remove, deprecate, rename or break a feature, flag, API or config key. Use whenever the user wants to delete or change existing behavior, even if they only say "clean up".
---
# Removing features

Before you break something, decide who pays for the move.

1. Split by surface. Library API, CLI flag, config file and UI are separate promises.
2. Find the core. If outside code calls it and you cannot fix that code, keep the name. Stub it instead.
3. Pick who pays:
   - Nobody: wait until almost no one uses it. Ask in public. Set a date and a condition.
   - You, by hand: fix the callers yourself.
   - You, by machine: alias the old name, or add a setting to go back.
4. Go in steps: warn, turn off by default, delete.
5. Write down the date and how to undo.

Output: one row per surface with keep / change / remove, who pays, next step.

Patterns across projects' public records. Proof and limits: `references/evidence.md`.
