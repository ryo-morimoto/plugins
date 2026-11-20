# Maintenance

Read only when editing the skill.

## Limits
- `SKILL.md`: 1000 characters, frontmatter included.
- Every other file: 2000 characters.
- After any edit run `python scripts/check_limits.py`. It also fails if a reference file is not linked from `SKILL.md`. Fix and rerun until it passes.

Small files force one topic per file and keep each load cheap. If a file is full, split it; do not raise the limit.

## Layout rules
- `SKILL.md` is a router: when to read which file. No method content there.
- One topic per reference file. Link every reference directly from `SKILL.md`; never chain file to file, because nested files get read partially.
- New axis: add it to the matching `axes-*.md`. If that file is full, create `axes-<topic>.md` and add one line to `SKILL.md`.
- New lesson from a session: add one entry to `failure-modes.md` in the form symptom, why, fix.
- Axis numbers are stable identifiers. Do not renumber; append.

## Writing rules
- English, imperative, with a reason for each rule, so the model can handle cases the rule did not foresee.
- Add only what the model does not already know.
- One term per concept: proposition, rival, scenario, operation, verdict, result, mode, state block.
- No dates or version notes.
- The description in `SKILL.md` is the trigger. Third person, what it does plus when to use it.

## Testing
- `evals/` holds test cases, one folder each. They are not packaged.
- Before changing behaviour, add or update a case that shows the gap. Run it with and without the skill.
- Watch real sessions: a file never read is badly signposted or unneeded; a file read every time may belong in `workflow.md`.
- Evals cap replies at 2000 characters in Japanese and 3000 in English. Count with Python `len`, never `wc -m`: under a POSIX locale it counts bytes and triples Japanese lengths.

## Release checklist
- [ ] `check_limits.py` passes
- [ ] Terms consistent
- [ ] Each new rule has a reason
- [ ] Evals rerun
