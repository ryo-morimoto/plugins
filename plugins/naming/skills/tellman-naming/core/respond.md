# How to answer

## When writing or editing code, or asked to change names

Apply this silently; explain only when asked. A request to rename, delete or merge means apply the changes (`audit.md`), not list them.

## When asked to review or advise

For each name, briefly:

1. Verdict: do not create / delete / merge / change / keep
2. Who reads it (how deep the code is, who the readers are)
3. Sense: what the name promises over time
4. Reason, using the row number from `review.md` or the rule from `avoid.md`
5. If changing: the new name, and what the change costs

- If you do not know who reads the code or what is likely to change, ask before answering. If you cannot ask, state your assumption.
- If readers stumble on a name, first state its meaning in documentation and conversation. Rename only if readings still diverge.
- Where this skill disagrees with common naming advice, follow the skill and note the disagreement in one line.

## Not covered

Product and brand names; migrating released names over many releases; how to get a team to agree; research on name length. Say so rather than stretch the rules.

Source: Zachary Tellman, *Elements of Clojure* (2019). https://elementsofclojure.com/
