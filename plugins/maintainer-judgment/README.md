# maintainer-judgment

> **検証中（experimental）です。** より良いスコープに組み替える可能性が高く、名前・構成は、予告なく変わります。

Four small skills for product and interface decisions. Each one is a pattern seen across several open source projects, sorted by situation type, not by person.

| Skill | Use it when | Situation types | Status |
|---|---|---|---|
| planning-breaking-changes | You want to delete, rename or break something | T1 library API, T2 user-facing config | mostly confirmed |
| triaging-contributions | You must answer a request or a pull request | T7 replies to contributions | confirmed |
| choosing-defaults | You pick what happens out of the box | T2 config, T4 desktop app | partly confirmed |
| native-vs-custom-ui | A standard UI part is not enough | T4 desktop app | single source |

"Confirmed" means: supported by records from two or more independent projects, with few counterexamples. It does not yet mean "predicts well".

## Honest limits

- These are patterns inferred from public records. They are not statements by any person, and no skill imitates a specific person.
- Most evidence was picked, not sampled at random.
- Each skill has a `references/evidence.md` with counts, sources and gaps.
- Projects behind the evidence: curl, Ghostty, Datasette, Rails/37signals products, Buttondown, Plausible.

## インストール

```
/plugin install maintainer-judgment --marketplace ryo-morimoto/plugins
```

claude.ai に同じ skill を上げている場合は、そちらを外してください。同じ名前の skill が 2 つ並びます。
