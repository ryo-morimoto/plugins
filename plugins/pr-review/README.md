2026-11-20 に、次のコマンドで、インストールを確認しました。新しいセッションから、skill と agent が見えること、skill が読み込めることまで確認しています。

```
claude plugin marketplace add ryo-morimoto/plugins
claude plugin install pr-review@ryo-morimoto-plugins --scope user
```

- `ryo-morimoto/plugins` の形は、内部で SSH（`git@github.com:…`）で clone されました。SSH の鍵が無い環境では、失敗する可能性があります。HTTPS の URL での追加は、試していません。
- skill の自動起動（質問から、自動で選ばれるか）と、`evaluator` の実際の呼び出しは、未確認です。

# pr-review

> **検証中（experimental）です。** より良いスコープに組み替える可能性が高く、名前・構成・記録の書式は、予告なく変わります。

## 目的

PR のレビューで、チームのメンタルモデル（システムの作りと、暗黙のルールの共通理解）を育てることが、主な目的です。リスクの検知は、副の目的です。

人が読んで判断する部分は、自動化しません。エージェントは、下準備、下書き、確認を担います。**投稿は、承認のあとに人が行います。**

この plugin の最初の一片は、「気づきを集め、優先づけの案を出し、下書きを作り、独立した確認を経て、承認できる状態にする」ところまでです。投稿の手順（`publish`）と、投稿を止める hook は、まだありません。

## 構成

| 部品 | 種類 | 内容 |
| --- | --- | --- |
| `draft-review-comments` | skill | 下書きを作る手順（`skills/draft-review-comments/SKILL.md`） |
| `import-findings.py` | script | pr-tour の JSON 書き出しを、リポジトリの内容と照合してから、記録として取り込む |
| `resolve-permalinks.py` | script | 固定リンクの行の存在と本文を確かめる（関連性は確かめない） |
| `validate-records.py` | script | 記録が書式に合うかを検査する |
| `render-review-html.py` | script | 下書きを、文や語句にコメントできる HTML にする（結果は「Copy for AI」で書き出す） |
| `evaluator` | agent | 下書きを、基準に照らして独立に評価する（読み取り専用） |
| `references/records.md` | 参照 | 記録の書式 |
| `references/rules.md` | 参照 | コメントを書く規則（作者個人の基準） |
| `references/intake.md` | 参照 | 気づきの取り込み方 |

スクリプトは `skills/draft-review-comments/scripts/`、テストは `tests/` にあります。

`import-findings.py` は、公開されているツール [pr-tour](https://github.com/YunSinLee/pr-tour)（MIT）が書き出す JSON（v1）を読みます。この plugin は、pr-tour の作者とは関係がありません。

## 対応するツールと、ファイルの形

標準の形（[Agent Plugins 1.0](https://agent-plugins.org/)）に寄せた部分と、Claude Code 向けの部分に分かれています。

| ファイル | 形 | 内容 |
| --- | --- | --- |
| `plugin.json`（plugin の根） | Agent Plugins 1.0 | 標準の manifest。`$schema` と `name` が必須 |
| `skills/draft-review-comments/` | Agent Skills | skill。スクリプトと参照を含む |
| `.claude-plugin/plugin.json` | Claude Code | Claude Code の manifest。**根の `plugin.json` とは別の形式で、同じファイル名** |
| `agents/evaluator.md` | Claude Code | サブエージェントの定義。Agent Plugins 1.0 の範囲外 |

- この文書の「agent」は、Claude Code のサブエージェントを指します。標準の「agent」は、ツール（クライアント）を指します。
- **動作を確認しているのは、Claude Code だけです。** 他のツールでは、未確認です。
- 根の `plugin.json` が標準の schema に合うかは、機械的には検証していません。Claude Code の `claude plugin validate` は、根の `plugin.json` を足したあとも通りました。

## 使い方の流れ

1. 問いと動機を確認する。
2. 気づきを取り込む（`references/intake.md`）。
3. 事実を集める。固定リンクを `resolve-permalinks.py` で確かめる。
4. 優先づけの案を出す。決めるのは人で、決めたら assessment を記録する。
5. 3 部形式で下書きを作る。
6. `evaluator` に確認してもらい、指摘は自分で確かめてから取り込む。
7. 人が承認する。
8. `validate-records.py` で記録を検査する。
9. 投稿は、承認のあとに人が行う（この plugin は投稿しない）。

詳しい手順は `skills/draft-review-comments/SKILL.md` にあります。

## 記録の書式

`skills/draft-review-comments/references/records.md` を見てください。1 件の記録を 1 つのテキストファイルにする書式です。

## ローカルで試す方法（Claude Code の場合）

次の形で試す想定です。**この手順は、実際には試していません。**

```
/plugin marketplace add <このリポジトリのパス>
/plugin install pr-review@ryo-morimoto-plugins
```

`claude plugin validate` は、plugin と marketplace の両方で成功しました（2026-11-20）。静的な検査と、skill・agent の検出までで、実行時の挙動は検証していません。

スクリプトのテストは、リポジトリの根で次のコマンドで実行します。2026-11-20 に、Python 3.9.6、3.14.10、3.15.2 のそれぞれで、120 件が通ることを確認しました（合成データのみ）。

```
python3 -m unittest discover -s plugins/pr-review/tests -v
```

## 評価の方針

部品ごとに、別の種類の作業や、別の人が、変更なしに使えるかを見ます。

## 現状と制限（検証中）

まだ決まっていない点と、すでに分かっている制限です。「着手の条件」があるものは、その条件が起きたときに、issue にします。

1. 記録の「不変」の原則と、後から埋める欄（`dismissed_reason`、`withdrawn_at`、`approved_*`、`outcome`、`reply_refs`）が矛盾している。事象を別ファイルに分けるほうが厳密だが、ファイルが増える。今は「1 回だけ埋められる欄」で割り切っている。 着手の条件: 実際の記録で、後から値を書く場面が最初に起きたとき。
2. 重要度（`importance`）の意味が、一部だけ定義されている。`rules.md` が、「低め」は認識共有のみ、「対応をお願いしたい」は「中くらい」以上、という関係を定めている（`records.md` の `low`／`mid`／`high` との対応づけの明記はない）。「高」のときに既定のアクションがどう変わるかは未定義。段階 1 では、人が決める。 着手の条件: 実際の PR レビューで、重要度を最初に付けるとき。
3. `/code-review` の出力の取り込みが、実際の出力で検証されていない。
4. 再レビュー（`recheck`）の手順が未定義。古い位置から新しい位置への対応づけと、判断の主体が決まっていない。段階 2。 着手の条件: 更新された PR を、最初に再レビューするとき。
5. `theme_key` のラベルの統一（語彙の管理）が無い。 着手の条件: 同じ話題のラベルが、2 つ以上の PR で食い違ったとき。
6. 共有の置き場所と、ローカルからの移行が未決。 着手の条件: 2 人目が、使い始めるとき。
7. 既存の別形式のメモとの関係は未決。`--store` には、既存のファイルと混ぜない別のディレクトリを指定することを勧める。
8. 投稿の手順（`publish`）と、投稿を止める hook は未作成。設計は概ねあるが、hook の挙動が未検証で、まだ必要になっていないので作っていない。 着手の条件: 承認前の投稿や、二重の投稿が、もう 1 回起きたとき。
9. （解決済み）
10. `evaluator` の独立性（同じモデルの別インスタンスが、独立した確認になるか）が未検証。評価の基準も、使用実績が少ない。 着手の条件: 2 つ目のツールで、実際に使うとき。
11. `SKILL.md` の移植性が未検証。frontmatter を `name` と `description` だけにしているが、標準の仕様を全文確認していない。Claude Code 以外での動作は未確認。 着手の条件: 2 つ目のツールで、実際に使うとき。
12. `rules.md` は作者個人の基準で、チームの合意ではない。
13. （解決済み）
14. （解決済み）pr-tour の実物の JSON 書き出し（2026-11-20、4 件）で、取り込み、検査、`code` の照合が通った。合成データとの違いと、実物で未確認の形（`side: left`、複数行の選択、複数行の本文、CRLF）は、`references/intake.md` に書いた。
15. 3 部形式の適用範囲が、「中くらい以上」に限られる読み替えになっており、低めの指摘の書き方が未定義。この読み替えは、作者の解釈。 着手の条件: 低めの指摘を、実際に下書きするとき。
16. `evaluator` の「読み取り専用」は文章上の指示で、`tools` に Bash が含まれるため、書き込みを機械的には防いでいない。論文や記事を取得する手段もなく、外部の根拠は `unverifiable` になる。 着手の条件: 2 つ目のツールで、実際に使うとき。
17. skill の自動起動と、`evaluator` の呼び出しは、実際には試していない（インストールと skill の読み込みは、確認した）。Python は、3.9.6、3.14.10、3.15.2 でテストが通ることを確認した（それ以外は未確認）。

ライセンス: MIT（リポジトリの根の `LICENSE`）
