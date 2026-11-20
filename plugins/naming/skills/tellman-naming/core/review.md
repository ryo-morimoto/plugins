# Judging an existing name

Search every use first: a name is read at its uses. Then take the first row that applies.

| # | Check | Finding | Verdict |
|---|---|---|---|
| 0 | Should it exist (`avoid.md`) | Its value or body reads as well; it is never read; it is a layer with one user (`boundaries.md`) | Delete: inline or remove |
| 1 | Name against what it holds or does | Singular holds a collection, or the reverse. Reads as boolean but is not. Reads as pure but writes. Says exact but is approximate. Names one thing, does two | Change: misleading |
| 2 | Name against its neighbours | The same word is used nearby (same function, or anywhere in the file for file-level names and keys) for a different thing | Change one; say which and why |
| 3 | Local default (only if the user asked to match it; run `survey.md`) | Departs from a clear majority form, no reason stated | Change to the local form |
| 4 | Name read alone, at a use site | Admits things it cannot stand for, and something nearby could be mistaken for it | Change: too broad |
| 5 | Name against time | States storage, type or algorithm where the purpose would last longer | Change if internal; else note it |
| 6 | Name against other names | Another name stands for the same thing, and they are not expected to diverge (`terms.md`) | Merge into one |
| 7 | None of the above | | Keep |

- "Keep" is a real answer. A word you would have preferred is not a defect. Do not fill a quota.
- The form of the question does not change the verdict.
- Decide the verdict before the cost. A released, exported name is expensive: say "change", state the cost, leave the timing to the owner. Unreleased names are cheap.
- If readers read different things into a word, state its meaning in documentation first; split only if they still diverge.
