---
name: native-vs-custom-ui
description: Decides whether to use a platform's standard UI part or build a custom one. Use whenever the user weighs native components against custom widgets, or a standard part blocks a feature.
---
# Native or custom UI

Start native. Go custom when native costs more.

Pick the row that fits:

| Situation | Do |
| --- | --- |
| Native part exists | Use it |
| Platform has no such idea | Build it, follow platform habits |
| Exists but gets in the way | Replace it |
| Exists, lacks one thing | Small tweak, opt-in |
| Exists, limits pile up | Plan a custom part |

"Limits pile up" means these signs, not one loud request:

1. Your own product is inconsistent.
2. Many separate requests hit the same limit.
3. Your workaround keeps breaking.

After going custom: aim for 90% native feel. Stop adding options to the old workaround.

Output: row, signs seen, next step.

Patterns across projects' public records. Proof and limits: `references/evidence.md`.
