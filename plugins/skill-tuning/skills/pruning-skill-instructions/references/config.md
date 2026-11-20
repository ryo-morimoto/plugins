# experiment.json

All output paths are relative to the directory holding `experiment.json` (or `--root`).

| Key | Meaning |
|---|---|
| `trials` | Directory per trial, e.g. `["t1","t2","t3"]`. May point at existing run directories. |
| `conditions` | List of `{"name", "skill", "dirs"}`. `skill` is the absolute path of the skill folder to load, or omitted for no skill. The first condition is the one under test. `dirs` (optional) lists directory names to look in when scoring older runs. |
| `tasks` | List of `{"name", "prompt", "measures", "expect", "group"}`. |
| `measures` | Named measure definitions (below). |
| `layout` | Output path pattern. Default `{trial}/{task}/{cond}/{file}`; `{group}` is also available. |
| `preamble`, `footer` | Text put before and after each prompt. `{skill}` in the preamble becomes the condition's skill path. Defaults tell the agent to read the skill and to stay read-only. |
| `model`, `effort` | Not used by the script. Record what the runs used. |

## Tasks

- `prompt`: the full task. Write `{out}` where the output directory goes; name the output file in the prompt (`{out}/answer.json`).
- `measures`: names of the measures that apply to this task.
- `expect`: for `decision` tasks, the correct value (`"keep"`, `"change"`).
- `group`: optional sub-directory, for layouts that use `{group}`.

## Measures

Each has a `type` and a `file` (a glob inside the run's output directory).

| Type | Value per run | Extra keys |
|---|---|---|
| `decision` | 1 if the JSON field equals the task's `expect` | `field` (default `decision`) |
| `occurrences` | Number of regex matches in a source file | `patterns`: file extension -> list of multi-line regexes, or `"builtin:clj-bindings"` |
| `value-length` | Total length of all values in a JSON object | |
| `value-matches` | How many values match a regex | `regex`, `keys` (optional subset) |
| `value-differs` | 1 if a key differs from a value | `key`, `value` |

`score` sums each measure over its tasks, per condition and trial. `decision` is also broken down by `expect` value. A `-` means no readable output was found.

## Commands

| Command | Does |
|---|---|
| `prepare` | Writes `<trial>/run/NNN.md` and `manifest.json`, creates output directories |
| `missing` | Lists missing or unreadable outputs; exit code 1 if any |
| `score` | Prints the table and saves `results.json` |
| `compare` | Range test of the first condition against each other one; per-task lists for decisions |
| `reproduce` | Rescoring must equal the saved `results.json`; exit code 1 otherwise |
