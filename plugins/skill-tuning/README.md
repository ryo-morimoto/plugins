# skill-tuning

> **検証中（experimental）です。** より良いスコープに組み替える可能性が高く、名前・構成は、予告なく変わります。

Measures whether a skill's instructions change behaviour, and helps cut the ones that do not.

- **Skill** `pruning-skill-instructions`: the nine-step procedure (purpose, prior work, instruction inventory, tasks on real artifacts, isolated runs, mechanical scoring, three trials on two models, prune and confirm, report).
- **Script** `skills/pruning-skill-instructions/scripts/experiment.py`: `prepare`, `missing`, `score`, `compare`, `reproduce`. Python 3 standard library only.

Ask "evaluate this skill", "is this skill worth shipping" or "slim this skill down" to use it.

## インストール

```
/plugin install skill-tuning --marketplace ryo-morimoto/plugins
```

claude.ai に同じ skill を上げている場合は、そちらを外してください。同じ名前の skill が 2 つ並びます。
