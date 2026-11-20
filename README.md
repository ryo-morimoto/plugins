# plugins

> **検証中（experimental）です。** より良いスコープに組み替える可能性が高く、名前・構成・記録の書式は、予告なく変わります。

[Agent Plugins](https://agent-plugins.org/) の形に寄せた、agent plugin を置くリポジトリです。動作を確認しているのは、Claude Code だけです。

<!-- plugins:start -->
| plugin | 内容 |
| --- | --- |
| [pr-review](plugins/pr-review/README.md) | PR のレビューで、気づきの整理、優先づけの案、コメントの下書き、独立した確認までを助ける |
| [thought-experiments](plugins/thought-experiments/README.md) | 思考実験を一緒に回し、標準や論文の分類を軸にした地図で、空いているところと次の推論の方向を選べるようにする |
| [naming](plugins/naming/README.md) | Tellman の方法で名前を付ける・変える。範囲をまとめて直すときは、名前を数え上げ、指摘がなくなるまで繰り返し、判定を台帳に残す |
| [maintainer-judgment](plugins/maintainer-judgment/README.md) | 削除・名前変更、機能の要望への返答、既定値、標準の UI 部品か自作か、を判断するときの、複数の OSS で見られたパターン |
| [skill-tuning](plugins/skill-tuning/README.md) | skill の指示が振る舞いを変えているかを測り、効いていない指示を削る |
| [rust-perf-surgery](plugins/rust-perf-surgery/README.md) | Rust の性能改善を、システムの指標で測り、振る舞いが変わらないことを証明しながら進める |
<!-- plugins:end -->

plugin の使い方は、それぞれの README を見てください。

plugin を足すときは、`plugins/<name>/plugin.json`（Agent Plugins 1.0）と `.claude-plugin/marketplace.json` の 2 つだけを書き、`python3 tools/catalog.py render` で Claude Code の manifest とこの表を生成します。`check` は CI でも動きます。

ライセンス: MIT（`LICENSE`）
