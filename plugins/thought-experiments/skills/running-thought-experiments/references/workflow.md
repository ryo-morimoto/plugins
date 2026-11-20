# Workflow

One stage per reply, so the user can steer. Asked for all at once? Compress.

**Budget per reply:** about 350 words (1,500 Japanese characters). Cut detail before options.

## The record is data; te keeps it
`scripts/te.py` (Python 3.11+) holds the stages, rules and checks, so you need not remember them.
- Start: `te.py init <dir> --id <slug>`.
- **Before every reply:** `te.py next <dir>`. It names the stage, what is missing, the instructions for that stage, and ends with the state lines to paste. It is computed from the record, not memory.
- Write only through `te.py add <dir> <kind> --json '{...}'`. It validates each event (fields: `data/schema/v1.json`).
- Cite with `te.py source add <dir> <id> --url U` (or `--file` for a copy the user gave), with `--quote` and `--page`. It stores the sha256 and checks the quote. A source you could not get stays `obtained = none`; a premise citing it cannot be `empirical-checked`.
- Numbers come from `scripts/*.py` writing to `$TE_OUTPUTS`; run `te.py run <dir>` and cite `outputs/`.
- Stage C reviewers: `te.py brief <dir> --lens practitioner|method|outsider`, then `--record-response` (`independent-attack.md`).
- Before committing: `te.py check <dir>`, fix every ERROR; `te.py render <dir> --write`.

## Stages (te next shows the detail)
- **A, frame and probe:** terms, mode (name one or two not picked; `axes-purpose.md`), `value-checks.md`, three or more rivals with the opposite, setup flaw, one provisional probe. No verdict.
- **B, operate:** fixed, idealised, varied; one variable per operation; verdicts per rival.
- **C, attack and conclude:** fresh reviewers, then labelled premises; options side by side; the user chooses.
- **D, review:** compare with the prediction; close.

## End every reply with
- **Next moves:** three or more directions, plus room for their own. Not a yes/no.
- The state lines from `te next`.

On a redefinition, say which results fall and which survive, then add a `frame` with `supersedes`.
