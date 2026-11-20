# Independent attack

Use in stage C, and before any verdict you report as a conclusion.

## Why not attack it yourself
You built the argument, so you share its blind spots. A self-attack tends to confirm the frame and can even eliminate a correct option with a confident but wrong reason. Reviewers who never saw the history catch what the author cannot.

## How
1. Spawn two or three fresh subagents in parallel, not forks: a fork inherits your context and your anchoring.
2. Give each a different lens, such as a domain practitioner, the formal or method view, and the epistemology of the argument. Different lenses find different gaps; agreement across them is strong evidence.
3. Make each brief with `te.py brief <dir> --lens <lens>`: it holds only the question, the definitions, the claim, and the labelled premises. Save each reply with `--record-response`; te accepts an attack only when both files match their sha256. Leave out the history, your own attacks and rebuttals, and the eliminated options. Each of these tells the reviewer where not to look.
4. The brief asks for objections naming their target, a counter thought experiment, a better rival, confidence, and which facts were checked in primary sources.

## Handling the reports
- Judge every objection with a response from `axes-outcome.md` (surrender, bar, restrict, reinterpret, incorporate) and give the reason. Do not keep a claim just because it is yours.
- Weigh an objection more when reviewers with different lenses raise it independently.
- Treat their facts as unverified unless they say they checked them.
- Reopen any earlier elimination that rested on reasoning an objection overturns, and say so to the user.
- No subagent tool available? Attack the result yourself and record it with `reviewer: self`; stage C stays open until the user accepts it (a `decision` by `user` with `accepts`).
