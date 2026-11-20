---
name: choosing-defaults
description: Checks a default value, default behavior or new setting. Use whenever the user is deciding what happens out of the box, adding a config option, or changing an existing default.
---
# Choosing defaults

Goal: most people are happy without touching settings.

Go in order.

1. Is it dangerous? Keep it off by default, even if handy.
2. Who is "most people"? Count per group (OS, keyboard layout), not overall.
3. Is there proof the new default is better (bug reports, other apps)? No proof, no change.
4. Does it break a basic thing for a small group? Do not ship. Split the default by group.
5. Shipping? Add a way back and say why you changed it.
6. Can you keep it working for years? If not, drop it and point to another path.

Also: a feature nobody turned on should cost nothing.

Output: the default, the group it is for, the proof, the way back.

Patterns across projects' public records. Proof and limits: `references/evidence.md`.
