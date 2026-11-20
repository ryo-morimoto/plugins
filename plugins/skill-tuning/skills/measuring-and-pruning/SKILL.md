---
name: measuring-and-pruning
description: Measures whether each instruction in a skill changes behaviour, then prunes the ones that do not - instruction inventory, tasks on real artifacts, with/without runs in isolated subagents, 3 trials. Use when asked to evaluate, benchmark, slim down or decide whether to ship a skill, or to "check if this skill actually works".
---
# Measuring and pruning a skill

A skill's instructions have no value in themselves. Value is the problem the skill solves for its user. Every step serves one question: does this text change behaviour in the direction the user wants?

Never overwrite a version. Copy the skill to `v<n>/` before each change and keep every run directory.

The bundled script does the mechanical parts:

```
python3 <this skill>/scripts/experiment.py <prepare|missing|score|compare|reproduce> <workspace>/experiment.json
```

Describe the experiment once in `experiment.json` (format: `references/config.md`; starting point: `examples/experiment.json`).

Words used here: a **task** is one prompt with a known answer or a countable output. A **condition** is which skill is loaded (new, previous, none). A **run** is one task under one condition. A **trial** is one pass over every task under every condition.

## 1. State the purpose

Write one sentence: what should differ in the output when the skill is loaded? If the user objects that a change narrows the purpose, stop and restate the purpose with them.

## 2. Survey prior work

Survey existing skills, linters, guidelines and published evaluations for the same problem. Reuse their formats (decision tables, good/bad pairs, checklists) and evaluation methods. Adopt a source only if you obtained the original.

## 3. Inventory the instructions

List every instruction, one row each, and classify:

| Class | Meaning | Default |
|---|---|---|
| Reminder | The model does this unprompted | Drop |
| New knowledge | The model would not know it | Keep |
| Preference | Goes against the model's default | Keep; these carry the skill |
| Duplicate | Said elsewhere in the skill | Drop |
| Background | Explains, does not direct | Drop unless it prevents misuse |

Count rows by script. Replace coined terms with widely used technical or everyday words. Get the user's approval of the keep/drop list before rewriting.

## 4. Build tasks on real artifacts

Prompt-only tasks are armchair theory: the model must read real source, files or documents.

- Take ground truth from history. A real before/after change by a trusted author gives two tasks: the before state expects "change", the after state expects "keep".
- Ask for one binary decision about one named item (`decision` measure). Open formats hit a floor or a ceiling and hide the effect.
- Add generation tasks whose output can be counted (`occurrences` and `value-*` measures).
- Split development tasks from held-out tasks. Record why each held-out task was chosen before any run. Decide to ship on held-out results only.
- Pilot five tasks with one trial. If both conditions score near 100% or near 0%, change the format before scaling.

## 5. Run in isolated subagents

1. `experiment.py prepare` writes one file per run (`<trial>/run/NNN.md`) with a fixed output path, and a `manifest.json` saying which run is which.
2. Launch one fresh subagent per file, with only this prompt: `Read <file> and do exactly what it says. Reply only 'done'.` Use the model and effort the user names. At most 20 per turn, in the foreground.
3. `experiment.py missing` lists missing or unreadable outputs. Rerun those before scoring.

Conditions are usually: new skill, previous version, no skill. The first condition in `experiment.json` is the one under test. If a subagent misuses a tool, do not clean up on its behalf: tell the user.

## 6. Score mechanically

- `experiment.py score` prints one value per trial for each measure and condition, and saves `results.json`. Never score by reading.
- Before comparing with an earlier experiment, run `experiment.py reproduce` on it. Its rescoring must print `reproduced`. If a value changed because a pattern changed, say so in the report.

## 7. Separate effect from noise

`experiment.py compare` prints, per measure, the range of each condition across trials:

- `SEPARATED`: ranges do not overlap. With three trials, treat as an effect.
- `overlap` or `identical`: no demonstrated effect.

For decisions it also lists tasks right only with the skill, right only without it, and wrong in every trial under both. The last group is out of the skill's reach.

One trial proves nothing at small n: run three. Repeat on a second model and report which effects hold on both.

## 8. Prune and confirm

- Cut instructions whose measure is `identical` across conditions.
- Every cut needs a run of the cut version. Check the measures that should not move.
- If a cut moves something that was not being measured, tell the user and offer to restore that one item.

## 9. Report

Lead with the verdict. Then one table of trial values per condition, what reproduced, what did not, and the limits (trials, n, scoring method, quality of ground truth). End with the one decision the user must make and a recommendation. Do not install or distribute the skill until the user says so.
