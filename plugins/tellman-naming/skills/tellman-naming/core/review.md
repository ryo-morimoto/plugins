# Judging an existing name

Run `survey.md` first. Then take the first row that applies.

| # | Check | Finding | Verdict |
|---|---|---|---|
| 1 | Name against what it holds or does | Singular name holds a collection, or the reverse. Reads as a boolean but is not. Reads as a pure function but writes. Says exact but is approximate. Names one thing but does two | Change: misleading |
| 2 | Name against its neighbours | The same word is used nearby for a different thing | Change one of them; say which and why |
| 3 | Name against the local default | It departs from a clear majority form, and no reason is stated nearby | Change to the local form |
| 4 | Name read alone, at a use site | It admits things it cannot stand for, and something nearby could be mistaken for it | Change: too broad |
| 5 | Name against time | It states storage, type or algorithm where the purpose would stay true longer | Change if internal; otherwise note it |
| 6 | None of the above | | Keep |

Rules for the verdict:

- "Keep" is a real answer. A word you would have preferred is not a defect. Do not fill a quota of changes.
- The form of the question does not change the verdict. "Keep or change this one?" and "what would you change?" get the same answer for the same name.
- Decide the verdict before the cost. Then report cost: an internal name is cheap to change; an exported one is expensive. For an exported name with a row 1 to 4 finding, say "change", state the cost, and leave the timing to the owner.
- If readers seem to read different things into a word, recommend checking what each means by it before renaming. First state the meaning in documentation; split into two names only if they still diverge.
