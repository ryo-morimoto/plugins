# Evidence: triaging feature requests

Situation type T7: replies to outside contributions in an open source project. Read this when the user asks "why".

## Confirmed (two projects)

Replies are mostly "yes, if" or "try over there", not yes or no. Clear rejection on the merits is rare.

| | Count |
| --- | --- |
| Support (conditions, questions, redirects) | 25 |
| Counterexamples (clear rejection on the merits) | 2 |
| Projects | curl, Ghostty |

Kinds of condition seen: rebase and tests, docs, a short consistent name, opt-in for risky things, keep existing behavior, use an existing option instead of a new one.

Kinds of redirect seen: an existing setting or flag, the OS, a shell tool, a plugin or library, a more general mechanism.

## What predicted direction (one project)

- Additions that overlap something existing get redirected.
- Niche convenience features from outside get questions.

## Why "read the diff"

Predictions from titles alone guessed conditions no better than a naive "ask for rebase, docs and tests on everything" (8 of 28 against 9 of 30). Read the real change first.

## Limits

- Ten-case tests cannot rule out luck.
- One project's sample mixes picked and unpicked items. The other is nine requests taken newest first.
- The outcome of a request depends a lot on whether the author keeps going, not only on the first reply.
- Present as patterns from public records, never as anyone's words.
