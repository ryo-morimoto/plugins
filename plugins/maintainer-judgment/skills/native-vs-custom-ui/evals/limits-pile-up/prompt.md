---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Our Windows/macOS design app uses the OS file picker. Five different requests are stuck on it: previews for our file format, tags, recent projects, cloud files, and a pinned folder list. Our floating 'quick open' window can't use the OS picker at all. And the preview hack we injected into the macOS picker broke in the last two OS updates. Do we build our own picker?
