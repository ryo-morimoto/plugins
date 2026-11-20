# Naming decisions

Recorded verdicts for plugin and skill names (`plugins/naming/skills/tellman-naming/core/decisions.md`). Look a name up here before renaming it again. Rows are judged by the rules in `core/` alone (`review.md` row 3, the local default, was not used).

| name | verdict | now | reason | date |
|---|---|---|---|---|
| `drafting-issue-records` | rename | `evaluating-issue-reports` | row 4: read alone it reads as drafting an issue to file, and `draft-review-comments` (drafts text to post) invites the same reading; row 5: "records" is the output format, evaluating is the purpose | 2026-11-21 |
| `triage` (description and keyword of issue-understanding) | rename | `issue-evaluation` (keyword); removed from the description | row 2: maintainer-judgment uses "triage" for deciding how to answer a request; both handle feature requests, so the same prompt could trigger either | 2026-11-21 |
| `triaging-feature-requests` | rename | `triaging-contributions` | row 1: the skill also handles pull requests and proposals ("read the diff"); its evidence file calls the situation "replies to outside contributions" (T7). Released: invocation name changes for installed users | 2026-11-21 |
| `removing-features` | rename | `planning-breaking-changes` | row 1: the skill also covers renaming, deprecating and breaking flags, APIs and config keys ("Before you break something"); a user renaming a key would not pick it by name. Released: invocation name changes | 2026-11-21 |
| `measuring-and-pruning` | rename | `pruning-skill-instructions` | row 4: read alone it does not say what is measured or pruned, and `rust-perf-surgery` (measures, removes work) could be mistaken for it; row 5: measuring is the method, pruning instructions without effect is the purpose. Released: invocation name changes | 2026-11-21 |
| `issue-understanding` | keep | | rows 0, 1, 2, 4, 5, 6 checked: one plugin for understanding and evaluating issues; no neighbour uses the word; the plugin may hold more than its one skill, so it is not merged with `evaluating-issue-reports` | 2026-11-21 |
| `evaluating-issue-reports` | keep | | rows 0, 1, 2, 4, 5, 6 checked: it evaluates evidence and drafts judgments; final decisions stay with a human, as its first line says | 2026-11-21 |
| `maintainer-judgment` | keep | | rows 0, 1, 2, 4, 5, 6 checked: patterns from maintainers' decisions; no neighbour uses "judgment" for another thing | 2026-11-21 |
| `choosing-defaults` | keep | | rows 0, 1, 2, 4, 5, 6 checked: checks a default value or behaviour, nothing else | 2026-11-21 |
| `native-vs-custom-ui` | keep | | rows 0, 1, 2, 4, 5, 6 checked: decides between a platform part and a custom one; the name states both sides | 2026-11-21 |
| `naming` | keep | | rows 0, 1, 2, 4, 5, 6 checked: broad (product and brand naming are not covered by its skill), but nothing nearby could be mistaken for it (row 4 needs both) | 2026-11-21 |
| `tellman-naming` | keep | | rows 0, 1, 2, 4, 5, 6 checked: names the method it follows; the plugin may take other naming skills, so not merged with `naming` | 2026-11-21 |
| `pr-review` | keep | | rows 0, 1, 2, 4, 5, 6 checked: supports a human's PR review; posting stays with the human | 2026-11-21 |
| `draft-review-comments` | keep | | rows 0, 1, 2, 4, 5, 6 checked: drafts review comments for approval; "review" is narrowed by the plugin `pr-review` at every use | 2026-11-21 |
| `rust-perf-surgery` | keep | | rows 0, 1, 2, 4, 5, 6 checked: plugin and skill share one sign for one thing, not two names | 2026-11-21 |
| `skill-tuning` | keep | | rows 0, 1, 2, 4, 5, 6 checked: tunes skills by measuring and pruning; no neighbour uses "tuning" | 2026-11-21 |
| `thought-experiments` | keep | | rows 0, 1, 2, 4, 5, 6 checked: holds the skills for running and mapping thought experiments | 2026-11-21 |
| `running-thought-experiments` | keep | | rows 0, 1, 2, 4, 5, 6 checked: runs one experiment; `mapping-thought-experiments` names the other activity on the same target | 2026-11-21 |
| `mapping-thought-experiments` | keep | | rows 0, 1, 2, 4, 5, 6 checked: maps a question space across experiments; distinct from running one | 2026-11-21 |
