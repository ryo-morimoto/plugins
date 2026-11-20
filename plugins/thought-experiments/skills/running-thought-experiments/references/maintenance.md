# Maintenance

Read only when editing the skill.

## Limits
- `SKILL.md`: 1000 characters, frontmatter included.
- Every other file: 2000 characters. `scripts/` and `data/` are run, not read, so `check_limits.py` limits each text te prints instead.
- After any edit run `python scripts/check_limits.py` (it also fails on a reference not linked from `SKILL.md`) and the tests in `tests/`.

If a file is full, split it; do not raise the limit.

## Layout rules
- `SKILL.md` is a router: when to read which file.
- One topic per reference file. Link every reference directly from `SKILL.md`; never chain file to file, because nested files get read partially.
- New axis: add it to the matching `axes-*.md`. If that file is full, create `axes-<topic>.md` and add one line to `SKILL.md`.
- New lesson from a session: if a check can catch it, add a rule to `data/rules.toml` with a test; else one entry in `failure-modes.md` (symptom, why, fix).
- Axis numbers are stable identifiers. Do not renumber; append.

## Writing rules
- English, imperative, with a reason for each rule, so the model can handle cases the rule did not foresee.
- Add only what the model does not know.
- One term per concept: proposition, rival, scenario, operation, verdict, result, mode, state block.
- No dates or versions.
- The description in `SKILL.md` is the trigger. Third person, what it does plus when to use it.

## Testing
- `evals/` holds test cases, one folder each. They are not packaged.
- Before changing behaviour, add or update a case that shows the gap. Run it with and without the skill.
- Watch real sessions: a file never read is badly signposted; one read every time belongs in `workflow.md`.
- Evals cap replies at 2000 characters in Japanese and 3000 in English. Count with Python `len`, not `wc -m` (bytes under a POSIX locale).

## Release checklist
- [ ] `check_limits.py` passes
- [ ] Terms consistent, tests pass
- [ ] Each new rule has a reason
- [ ] Evals rerun
