# rust-perf-surgery

> **検証中（experimental）です。** より良いスコープに組み替える可能性が高く、名前・構成は、予告なく変わります。

Rust の性能改善（CPU、メモリ、IO、キャッシュ、再利用、データ構造の選択）で、システム全体の指標を動かし、振る舞いが変わらないことを証明する skill を 1 つ持つ plugin です。振る舞いを変える高速化は不具合、指標を動かさない高速化は無駄、と扱います。

## 構成

| 部品 | 内容 |
| --- | --- |
| `skills/rust-perf-surgery/SKILL.md` | 手順（目標 → 契約 → 基準値 → 診断 → 操作 → 証明 → 確認）と、各段で読むファイル |
| `references/` | 診断（CPU、メモリ、IO、仕事の要否）、操作、証明のゲート、報告の書式、出典 |

## インストール

```
/plugin install rust-perf-surgery --marketplace ryo-morimoto/plugins
```

claude.ai に同じ skill を上げている場合は、そちらを外してください。同じ名前の skill が 2 つ並びます。
