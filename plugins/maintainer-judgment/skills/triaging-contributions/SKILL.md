---
name: triaging-contributions
description: Drafts a maintainer-style reply to a feature request, proposal or pull request. Use whenever the user asks whether to accept, reject or how to answer a request, even if they only paste an issue.
---
# Triaging contributions

A good reply is rarely yes or no. It is "yes, if" or "try over there".

1. Read the real thing: the diff and the description. Not just the title.
2. Does it copy something that exists? Point to the existing way.
3. Does it change a promise other code relies on? Stop and ask why.
4. Do several requests hit the same wall? Fix the wall once.
5. Risky or in most people's way? Make it opt-in.
6. If no: say no plainly and give another path (setting, OS, plugin).
7. If yes: name the conditions (docs, tests, a short consistent name, keep old behavior).

Output: direction (welcome / question / redirect), conditions, where to redirect.

Patterns across projects' public records. Proof and limits: `references/evidence.md`.
