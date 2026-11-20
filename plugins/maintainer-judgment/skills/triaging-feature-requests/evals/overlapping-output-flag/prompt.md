---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I maintain a small CLI that prints query results. It already has `--json`. Someone opened this issue: 'Please add `--jsonl` so each row is one JSON object per line. I pipe the output into another tool and have to run jq -c .[] every time. Happy to send a PR.' How should I reply?
