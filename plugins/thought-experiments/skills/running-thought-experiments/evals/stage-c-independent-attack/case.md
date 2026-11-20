# Case: stage C attack comes from fresh subagents

## Setup
A run has reached stage C after several stage B replies. The agent holds a conclusion it built itself, plus earlier eliminations it made on its own reasoning.

## Prompt
"Stage C に進み、ここまでの全体の結論を、反例となる思考実験で攻撃する。"

## Gap this case shows
Without the rule, the agent attacks its own result. In the source session this self-attack wrongly eliminated a correct option (a conditional theorem with an explicit trusted base) as question-begging. Three fresh reviewers, briefed only with the claim and premises, each found the error independently.

## Pass criteria
- Spawns two or more fresh subagents (not forks) in parallel, each with a different lens.
- Each brief holds the question, definitions, claim and labelled premises only: no history, own rebuttals or eliminated options.
- The reply judges every returned objection with a named response (surrender, bar, restrict, reinterpret, incorporate) and a reason.
- Earlier eliminations that an objection overturns are reopened and named.
- Reviewer facts not checked by a tool are marked unverified.

## Fail signals
- The agent writes the attack itself while a subagent tool is available.
- A brief includes the agent's own attack history or eliminated options.
