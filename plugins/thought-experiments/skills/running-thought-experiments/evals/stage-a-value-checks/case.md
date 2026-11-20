# Case: stage A checks for a known answer and a strawman

## Setup
The user wants a socially valuable thought experiment about disaster policy. Public typhoon statistics (counts per year, 75 years) are available. No earlier run.

## Prompt
"「気候の変化が統計的に検出されていない」ことを、防災で「変化なし」として扱ってよいか、思考実験したい。"

## Gap this case shows
In the source session the run passed every stage, then the user called the result obvious. The conclusion (absence of evidence is not evidence of absence; a detection threshold implies a loss ratio near 1) is textbook decision theory, and an expert paper had already used a weaker criterion for the same reason. The attacked proposition ("non-detection means no change, so keep the design") turned out, in stage B, to be held by no official document.

## Pass criteria
- Before listing rivals, searches for an existing answer and reports what it found, or says nothing was found and how it searched.
- In destructive mode, names who holds the attacked proposition with a source, or flags it as a strawman and moves to a held position.
- Writes a prediction of what an informed practitioner would expect, and keeps it for stage C.
- If the answer is already known, proposes a sharper question instead of proceeding as if it were open.

## Fail signals
- Rivals are listed without any search for prior answers.
- The attacked proposition has no holder and the reply does not say so.
- No prediction is recorded.
