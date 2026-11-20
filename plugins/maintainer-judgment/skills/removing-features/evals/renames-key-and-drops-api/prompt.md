---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We ship a CLI plus a Python library (about 2,000 installs a week on PyPI). For the next release I want to clean up three things: rename the config key `cache_dir` to `cache.path`, delete the `--no-color` flag (nobody on the team uses it), and remove `Client.fetch_all()` from the library because `Client.iter()` is better. Give me the plan.
