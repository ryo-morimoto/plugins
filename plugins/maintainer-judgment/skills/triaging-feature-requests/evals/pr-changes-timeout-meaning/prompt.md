---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

A contributor sent a PR to our HTTP client library. It changes `timeout=` from 'per read' to 'total request time' because 'that is what everyone expects'. Tests pass. The diff is 40 lines and touches the public `request()` function. Draft my review reply.
