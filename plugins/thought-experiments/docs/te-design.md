# 設計：思考実験の手順をデータとコードにする（`te`）

状態: 設計（未実装）。根拠: issue #30、#28、#29。

## 1. 問題

`running-thought-experiments` は、手順を散文（`workflow.md` と参照ファイル）で持ち、エージェントが読んで従うことを前提にしている。実セッション（issue #30）では、次のことが起きた。

- 参照ファイルは、`workflow.md` 以外ほとんど読まれなかった。`failure-modes.md` の「毎回見直す」は一度も実行されなかった。
- 価値の確認（#28）と独立した攻撃（#29）は、指示を足しても「やるかどうか」がエージェントの記憶に依存する。
- 用語の定義（散文）と計算（式）がずれた。孫引きの事実が前提に入り、後から6件以上訂正した。
- 段階B・C を fork に任せ、1件 34万〜61万トークンかかった。

hook は Agent Plugins 1.0.0 の範囲外（skills と MCP サーバーだけ）なので使わない。使えるのは、スキルに同梱するスクリプト（Agent Skills の `scripts/`）と、利用者のリポジトリの CI・pre-commit。どちらも pull 型（呼ばれたときに動く）なので、**呼ぶべき点を1つに減らし、手順そのものをコードとデータに移す**。

## 2. 方針：データ指向（Data-Oriented Programming の4原則）

| 原則 | この設計での形 |
| --- | --- |
| コードとデータを分ける | 実験の状態はファイル（データ）、手順と検査は純粋関数（コード）。関数は状態を持たない。入出力は CLI の端だけ |
| 汎用のデータ構造 | 記録は TOML と JSON Lines。読み込むと辞書とリストになる。専用のクラスを作らない |
| データは不変 | 記録は追記だけの出来事の列（イベント）。訂正も「訂正」という新しい出来事として足す。現在の状態は出来事の列を畳み込んで求める |
| スキーマと表現を分ける | 出来事の形はスキーマ（JSON Schema）で、段階の規則は規則データ（`rules.toml`）で別に持つ。手順を変えるときはコードではなく規則データを変える |

## 3. データ

### 3.1 利用者のリポジトリ（実験1本につき1ディレクトリ）

```
experiments/<YYYY-MM-DD-slug>/
  experiment.toml   # 変わらない身元：id、問い、ゴール（誰のどの判断）、開始日
  events.jsonl      # 追記だけの出来事の列（te add だけが書く）
  sources.toml      # 引用した資料：URL、sha256、取得日、ページ、引用文、一次か二次か
  scripts/          # 計算（定義と式を同じ場所に置く）
  outputs/          # scripts の出力（JSON）。te run が生成し、te check が再実行して照合する
  README.md         # 生成物（te render）。手で編集しない
```

### 3.2 出来事（`events.jsonl` の1行）

共通の欄: `id`（連番）、`at`（日時）、`kind`、`by`（`claude` / `user` / `reviewer:<lens>`）、`note`（自由な Markdown。考えた中身はここに書く）。

| kind | 主な欄 | 段階 |
| --- | --- | --- |
| `frame` | `terms`（用語と採った解釈）、`mode`、`modes_not_picked`、`flaw` | A |
| `prior_answer` | `found`（出典 id のリスト）か `searched`（検索した語と範囲） | A |
| `holder` | `proposition`、`sources`（その立場を取っている証拠）か `strawman: true` | A |
| `prediction` | `expected`、`confidence`、`by_whom` | A |
| `rival` | `rid`、`text`、`is_opposite` | A〜C |
| `probe` / `operation` | `scenario`（固定・理想化・変化）、`varied`、`result`、`eliminates`、`favours`、`sources`、`outputs` | A / B |
| `attack` | `by`（`fresh` / `self`）、`lenses`、`objections`（`premise`、`response`、`reason`） | C |
| `conclusion` | `answer`、`premises`（`text`、`label`、`sources`、`outputs`）、`options`（`status`、`reason`） | C |
| `correction` | `target`（出来事 id）、`what`、`why` | いつでも |
| `decision` | `what`（ユーザーが選んだこと） | いつでも |
| `branch` / `close` | `to` / `state`（`結論済み` / `中断`） | いつでも |

`label` は `definitional` / `argued` / `empirical-checked` / `empirical-unverified` / `value`。

### 3.3 プラグインに同梱するデータ

```
skills/running-thought-experiments/
  data/schema.json   # 出来事の形
  data/rules.toml    # 段階の規則（何がそろえば次へ進めるか、その段階で見せる短い指示）
  scripts/te.py      # CLI（標準ライブラリだけ）
```

`rules.toml` の例:

```toml
[[stage]]
id = "A"
requires = ["frame", "prior_answer", "holder", "prediction", "rival>=3", "rival.is_opposite", "probe"]
show = ["value-checks", "define-terms-by-formula"]

[[stage]]
id = "C"
requires = ["attack.by=fresh", "conclusion"]
show = ["independent-attack", "compare-prediction"]

[[invariant]]
id = "checked-needs-primary"
rule = "conclusion.premises[label=empirical-checked].sources -> sources[level=primary, sha256]"
message = "確認済みの前提は、sha256 付きの一次資料を参照する"
```

`requires` と `rule` の書き方は、小さな述語の集合に限る（存在、件数、欄の値、参照先の条件）。述語の実装は `te.py` の関数で、規則データは関数の名前と引数だけを持つ。汎用の言語は作らない。

## 4. コード

すべて純粋関数（データを受け取り、データを返す）。ファイルの読み書きとネットワークは CLI の端だけ。

| 関数 | 入力 → 出力 |
| --- | --- |
| `fold(events)` | 出来事の列 → 現在の状態（段階、対立仮説ごとの状態、前提、未検証の一覧）。訂正は対象の出来事を上書きせず、状態の計算で反映する |
| `next_step(rules, state)` | → 今の段階、足りないもの、見せる指示の id |
| `check(rules, state, sources, outputs)` | → 違反の一覧 |
| `brief(state, lens)` | → 文脈を持たない reviewer への依頼文。問い・用語・結論・前提（ラベル付き）だけを射影し、経緯と脱落した選択肢は構造上含まない |
| `render(state, sources)` | → `README.md` と、返答の骨組み（状態の行、次の一手） |

CLI:

| コマンド | 何をするか |
| --- | --- |
| `te next <dir>` | 今の段階、足りないもの、その段階の短い指示を表示する。**エージェントが覚えるのはこれだけ** |
| `te add <dir> <kind> --json '{…}'` | スキーマで検査してから追記する。記録を書くのはこのコマンドだけ |
| `te source add <dir> <url> --page … --quote …` | 取得して sha256 を取り、`sources.toml` に記録する。一次資料をたどる道を一番楽にする |
| `te brief <dir> --lens <名前>` | reviewer への依頼文を出す。fork より安く、独立性も高い |
| `te run <dir>` | `scripts/` を実行し、`outputs/` を作る |
| `te render <dir>` | `README.md` と返答の骨組みを生成する |
| `te check <dir>` | 規則と不変条件を検査する。`scripts/` を再実行して `outputs/` と照合する。終了コードで返す（CI と pre-commit 用） |

## 5. 失敗との対応

| issue #30 の失敗 | どこで防ぐか |
| --- | --- |
| 参照ファイルが読まれない | `te next` が段階に応じた指示だけを表示する。読むかどうかをエージェントに任せない |
| 価値の確認を飛ばす | 段階A の `requires` がそろうまで、`te next` は段階B に進まない |
| 自己攻撃、fork のコスト | 段階C の `requires` に `attack.by=fresh`。`te brief` が依頼文を作る |
| 定義と計算のずれ | 計算は `scripts/` に置き、記録の数値は `outputs/` から `render` が埋める。`te check` が再実行して照合する |
| 孫引き | 不変条件 `checked-needs-primary`。`te source add` |
| 群の差を因果と読む | 判断の問題なので、段階B で `show` する短い指示にとどめる |
| 返答の長さ・形 | `te render` が骨組みを生成する。長さは骨組みの範囲で守られる。本文の長さは守れない（限界） |
| 呼び忘れ | 利用者のリポジトリの CI と pre-commit で `te check` を走らせる。`te next` を呼ばなくても、コミットで止まる |

## 6. スキルの文章

`workflow.md` は「`te next` を実行し、表示に従う。記録は `te add` で書く」と、判断の質に関わる短い指示だけになる。段階ごとの指示は `rules.toml` の `show` が指す短い文に移し、`te next` が表示する。参照ファイル（`value-checks.md` など）の中身は、この短い文に分解する。`check_limits.py` は、規則データの文も検査の対象に加える。

## 7. 地図との関係

地図のセルの `evidence` は、実験のディレクトリを指す。`thought_map.py` は、実験の `fold` の結果（結論、状態）を読んでセルの状態と照合できる。地図と実験が同じ「構造化した状態 → スクリプト → 生成物」の型になる。

## 8. 段階的な導入

1. **最小の版:** `fold`、`next_step`、`check` と、出来事の `frame` / `prior_answer` / `holder` / `prediction` / `rival` / `operation` / `attack` / `conclusion` / `correction`。`te next`・`te add`・`te check`・`te brief` だけ。
2. **試す:** 既存の記録1本（ryo-morimoto/thought-experiments の `experiments/2026-11-21-life-value-in-flood-bc.md`）を出来事の列に移し、`te check` が既知の失敗（藁人形、自己攻撃、確認済みの根拠の欠落）を検出するかを確かめる。
3. **評価:** 評価ケースを複数回走らせ、`te next` が呼ばれる割合と、価値の確認と独立した攻撃が行われる割合を、散文版（現在の main）と比べる。
4. その後に `te source add`、`te run`、`te render`。

## 9. 決めていないこと

- 利用者のリポジトリの CI が `te.py` をどう入手するか（プラグインの固定したコミットを取得する、リポジトリに同梱する、など）。
- 出来事の列を JSON Lines にするか、TOML の配列にするか（追記と差分の見やすさ、人が読む頻度で選ぶ）。
- `note` の自由な Markdown の長さに上限を設けるか。
- 既存の Markdown の記録を移すか、新しい実験から使うか。
- 呼ばれる割合が低いと分かったときに、MCP サーバー（Agent Plugins 1.0.0 の範囲内）に移すか。
