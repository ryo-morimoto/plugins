# 設計：思考実験の手順をデータとコードにする（`te`）

状態: 設計（未実装、レビュー済み）。根拠: issue #30、#28、#29。第2版で、既存の標準の調査（11章）と、既存の記録1本を移した試し（12章）の結果を反映した。

## 1. 問題

`running-thought-experiments` は、手順を散文（`workflow.md` と参照ファイル）で持ち、エージェントが読んで従うことを前提にしている。実セッション（issue #30）では、次のことが起きた。

- 参照ファイルは、`workflow.md` 以外ほとんど読まれなかった。`failure-modes.md` の「毎回見直す」は一度も実行されなかった。
- 価値の確認（#28）と独立した攻撃（#29）は、指示を足しても「やるかどうか」がエージェントの記憶に依存する。
- 用語の定義（散文）と計算（式）がずれた。孫引きの事実が前提に入り、後から6件以上訂正した。一次資料で確かめ直すと、さらに誤りが見つかった（12章）。
- 段階B・C を fork に任せ、1件 34万〜61万トークンかかった。

hook は Agent Plugins 1.0.0 の範囲外（skills と MCP サーバーだけ）なので使わない。使えるのは、スキルに同梱するスクリプト（Agent Skills の `scripts/`）と、利用者のリポジトリの CI・pre-commit。どちらも pull 型（呼ばれたときに動く）なので、**呼ぶべき点を1つに減らし、手順そのものをコードとデータに移す**。

## 2. 方針

### 2.1 データ指向（Data-Oriented Programming の4原則）

| 原則 | この設計での形 |
| --- | --- |
| コードとデータを分ける | 実験の状態はファイル（データ）、手順と検査は純粋関数（コード）。関数は状態を持たない。入出力は CLI の端だけ |
| 汎用のデータ構造 | 記録は TOML と JSON Lines。読み込むと辞書とリストになる。専用のクラスを作らない |
| データは不変 | 記録は追記だけの出来事の列。訂正も新しい出来事として足す。現在の状態は出来事の列を畳み込んで求める |
| スキーマと表現を分ける | 出来事の形はスキーマ（JSON Schema 2020-12）で、段階の規則は規則データ（`rules.toml`）で別に持つ |

### 2.2 申告ではなく生成物で証明させる

自己申告の欄（「先行する答えを調べた」「文脈を持たない reviewer が攻撃した」）は、決定論の検査でも「書いたかどうか」しか確かめられない（12章の試しで確認）。そこで、やったことの証拠を **te 自身が生成するファイル** に残させ、出来事はそのファイルを sha256 で指す。偽った生成物までは防げないが、「やらなかった」と「やったと書いただけ」は区別できる。

### 2.3 一次資料だけを根拠にする

事実の根拠は、一次資料（著者自身の論文・著者稿、発行機関の公式文書）で確かめたものに限る。二次資料・孫引き・検索の要約は、一次資料を探す手がかりにとどめる。一次か二次かは出典ごとではなく **前提と出典の組ごと** に持つ（同じ文書が、ある事実には一次資料で、別の事実には孫引きになる。12章）。

## 3. データ

### 3.1 利用者のリポジトリ（実験1本につき1ディレクトリ）

```
experiments/<YYYY-MM-DD-slug>/
  experiment.toml   # 変わらない身元だけ：id、作成日。問いとゴールは出来事（frame）に置く（範囲の変更を記録するため）
  events.jsonl      # 追記だけの出来事の列（te add だけが書く）
  sources.toml      # 出典：URL、sha256、取得の経路、取得日、引用、ページ、取得できなかった記録
  notes/<id>.md     # 長い自由記述（出来事の note から参照する）
  briefs/<id>.md    # te brief が生成した reviewer への依頼文と、受け取った応答（sha256 で出来事から指す）
  scripts/          # 計算（定義と式を同じ場所に置く）
  outputs/          # scripts の出力（JSON）。te run が生成し、te check が再実行して照合する
  README.md         # 生成物（te render）。手で編集しない
```

### 3.2 出来事（`events.jsonl` の1行）

共通の欄: `id`（連番）、`v`（スキーマの版）、`at`（RFC 3339 の日時）、`kind`、`author`（`claude` / `user` / `reviewer:<観点>`）、`note`（短い自由記述。長いものは `notes/<id>.md`）。書き手の欄を `by` ではなく `author` にするのは、攻撃の `reviewer` 欄と取り違えないため（12章）。

| kind | 主な欄 | 段階 |
| --- | --- | --- |
| `frame` | `question`、`goal`（誰のどの判断）、`terms`（用語と採った解釈）、`mode`、`modes_not_picked`、`flaw`、`supersedes`（範囲を変えるとき、前の frame の id） | A（範囲の変更はいつでも） |
| `prior_answer` | `sources`（出典 id。`te source add` で取得したもの）、または `searched`（検索の語・範囲・結果件数）と `found: false` | A |
| `holder` | `rival`（対象の rid）、`sources`（その立場を実際に取っている文書・判断の記録）、または `strawman: true` | A |
| `prediction` | `distribution`（rid ごとの確率。合計1）、`by_whom`、`reference_class` | A（最初の operation より前だけ） |
| `rival` | `rid`、`text`、`is_opposite`、`would_reject_if`（何が出たら捨てるか） | A〜C |
| `probe` / `operation` | `scenario`（固定・理想化・変化）、`varied`、`result`、`verdicts`（rid ごとの `status` と `strength`）、`sources`、`outputs` | A / B |
| `attack` | `reviewer`（`fresh` / `self`）、`brief`（briefs/ のファイルと sha256）、`response`（同）、`objections`（`target`: premise / inference / conclusion、`ref`、`response`: surrender / bar / restrict / reinterpret / incorporate、`reason`）、`verdicts` | C |
| `conclusion` | `answer`、`answer_rival`（最終的に採った対立仮説の rid。採点に使う。どれも採らないなら null）、`claim`（実務者向けの主張）、`premises`（`text`、`label`、`if_false`、`citations`）、`options`（`text`、`downsides`）、`accepted_downsides`、`milestones`（何が観察されたら考えを変えるか） | C |
| `review` | `by_whom`、`value`（新しさ・重要さ・驚き）、`text`（事後評価、ユーザーによる価値の評価） | 結論の後 |
| `correction` | `target`（出来事 id または出典 id）、`what`、`why` | いつでも |
| `supersede` | `target`（出来事 id）、`why`（誤りの訂正ではなく、方針や範囲の変更） | いつでも |
| `decision` | `what`（ユーザーが選んだこと） | いつでも |
| `branch` / `close` | `from` / `to`、`state`（`結論済み` / `中断`） | いつでも |

`label` は `definitional` / `argued` / `empirical-checked` / `empirical-unverified` / `value`。`citations` は前提と出典の組で、`{source, level: primary|secondary, primary_of, role}` を持つ（`role` は CiTO から絞った語：`citesAsEvidence`、`usesDataFrom`、`usesMethodIn`、`supports`、`disputes`、`qualifies`）。

`verdicts` の `status` は `eliminated` / `weakened` / `unchanged` / `supported` / `undecidable`、`strength` は `direct` / `indirect`。対立仮説の現在の状態（生き残り・脱落）は手で書かず、`fold` が verdicts と未回答の反論から計算する（Carneades の proof standard の考え方。未回答の undercut がある仮説は「生き残り」にしない）。

### 3.3 出典（`sources.toml`）

```toml
[src.kawabata2023]
title = "Kawabata et al. 2023, JMSJ 101(6)"
url = "https://www.jstage.jst.go.jp/article/jmsj/101/6/101_2023-025/_pdf"
sha256 = "fbccd5b8…"
obtained = "fetch"            # fetch（te source add が取得）/ user（利用者が取得して渡した）/ none
retrieved = 2026-11-21
quotes = [{ page = 4, text = "From 1987 to 2007, …" }]

[src.knutson2019]
obtained = "user"             # 自動取得が拒否され、利用者が出版社の PDF を渡した。ファイルはリポジトリに入れない
sha256 = "23553233…"

[src.schwenk1990]
obtained = "none"
attempts = ["ScienceDirect 403", "Crossref に要旨なし"]   # 取得できなかった記録。これを引く前提は empirical-checked にできない
```

### 3.4 プラグインに同梱するデータ

```
skills/running-thought-experiments/
  data/schema/v1.json  # 出来事の形（版ごと）
  data/rules.toml      # 段階の規則と不変条件
  scripts/te.py        # CLI（標準ライブラリだけ）
```

`rules.toml` の例:

```toml
[[stage]]
id = "A"
requires = ["frame", "prior_answer", "holder(attacked_rivals)", "prediction",
            "rival>=3", "rival.is_opposite", "rival.would_reject_if", "probe"]
show = ["value-checks", "define-terms-by-formula"]

[[stage]]
id = "C"
requires = ["attack.reviewer=fresh", "attack.brief.exists", "attack.response.exists", "conclusion"]
show = ["independent-attack", "compare-prediction"]

[[invariant]]
id = "checked-needs-primary"
rule = "premise[label=empirical-checked].citations -> level=primary & source.sha256, or level=secondary & primary_of.sha256"
message = "確認済みの前提は、sha256 付きの一次資料を参照する（二次資料なら、たどった先の一次資料）"

[[invariant]]
id = "no-post-hoc-prediction"
rule = "prediction.id < first(operation).id"

[[invariant]]
id = "unobtainable-is-unverified"
rule = "citation.source.obtained=none -> premise.label!=empirical-checked"
```

述語は小さな集合に限る（存在、件数、欄の値、参照先の条件）。実装は `te.py` の関数で、規則データは関数の名前と引数だけを持つ。汎用の言語は作らない。

## 4. コード

すべて純粋関数。ファイルの読み書きとネットワークは CLI の端だけ。

| 関数 | 入力 → 出力 |
| --- | --- |
| `score(state)` | → 予想の採点。`prediction.distribution` と `conclusion.answer_rival` から、多クラスの Brier スコア（Σ(pᵢ − oᵢ)²、0 が最良、2 が最悪）と、採った仮説に置いた確率を返す。どちらかが欠けていれば採点しない |
| `upcast(event)` | 古い版の出来事 → 現在の版（`fold` の手前で必ず通す） |
| `fold(events)` | 出来事の列 → 現在の状態（段階、対立仮説ごとの状態、前提、未検証の一覧） |
| `next_step(rules, state)` | → 今の段階、足りないもの、見せる指示の id |
| `check(rules, state, sources, outputs, files)` | → 違反と警告の一覧 |
| `brief(state, lens)` | → reviewer への依頼文。問い・用語・結論・前提（ラベル付き）だけを射影する |
| `render(state, sources, fmt)` | → `README.md`、返答の骨組み、`--argdown` の書き出し |

CLI:

| コマンド | 何をするか |
| --- | --- |
| `te next <dir>` | 今の段階、足りないもの、その段階の短い指示を表示する。**エージェントが覚えるのはこれだけ** |
| `te add <dir> <kind> --json '{…}'` | スキーマで検査してから追記する。記録を書くのはこのコマンドだけ |
| `te source add <dir> <id> (--url <url> \| --file <path>) [--quote <text> --page <n>]…` | 取得（または利用者が渡したファイルを読み）、sha256・取得の経路・取得日を記録する。引用が取得した本文にあるかを照合し `quotes[].verified` に書く。取得できなければ `obtained = "none"` と試した経路を記録する。一次資料との対応は出典ではなく前提の引用（`citations[].primary_of`）に書く |
| `te brief <dir> --lens <名前>` | 依頼文を `briefs/<id>.md` に保存し、sha256 を表示する。lens の既定は「実務の専門家」「方法の専門家」「専門外の読み手」（英国防省 Red Teaming Handbook の、専門家と非専門家を混ぜる勧めに沿う） |
| `te brief <dir> --record-response <id> <file>` | reviewer の応答を保存し、sha256 を表示する |
| `te run <dir>` | `scripts/` を実行し、`outputs/` を作る |
| `te render <dir> [--argdown]` | `README.md` と返答の骨組みを生成する。`--argdown` は前提と結論を Argdown の記法で書き出す |
| `te check <dir>` | 規則・不変条件・警告を検査し、`scripts/` を再実行して `outputs/` と照合する。終了コードで返す（CI と pre-commit 用） |

`te check` の警告（止めはしない）: どの仮説の状態も変えなかった operation（診断性がない。ACH の考え方）、`varied` が2つ以上ある operation（te の手順違反）。

## 5. 失敗との対応

| 失敗 | どこで防ぐか |
| --- | --- |
| 参照ファイルが読まれない | `te next` が段階に応じた指示だけを表示する |
| 価値の確認を飛ばす | 段階A の `requires`。`prior_answer` は取得した出典か検索の記録を要求する |
| 藁人形 | `holder(attacked_rivals)`：攻撃や脱落の対象になった仮説そのものに、実在する立場の出典を要求する |
| 自己攻撃、fork のコスト | 段階C の `requires` に、te brief が生成した依頼文と応答のファイル（sha256）を要求する |
| 定義と計算のずれ | 計算は `scripts/` に置き、記録の数値は `outputs/` から `render` が埋める。`te check` が再実行して照合する |
| 孫引き | 不変条件 `checked-needs-primary`（二次資料なら一次資料をたどった先の sha256 まで要求）と `unobtainable-is-unverified` |
| 後から予想を書く | 不変条件 `no-post-hoc-prediction` |
| 群の差を因果と読む | 判断の問題なので、段階B で `show` する短い指示にとどめる |
| 返答の長さ・形 | `te render` が骨組みを生成する。本文の長さは守れない（限界） |
| 呼び忘れ | 利用者のリポジトリの CI と pre-commit で `te check` を走らせる |

限界: 偽った生成物（自分で書いた依頼文を reviewer の応答として保存する、など）は防げない。防げるのは「やらなかった」ことと「やったと書いただけ」の区別まで。

## 6. スキルの文章

`workflow.md` は「`te next` を実行し、表示に従う。記録は `te add` で書く」と、判断の質に関わる短い指示だけになる。段階ごとの指示は `rules.toml` の `show` が指す短い文に移し、`te next` が表示する。`check_limits.py` は規則データの文も検査の対象に加える。

## 7. 地図との関係

地図のセルの `evidence` は実験のディレクトリを指す。`thought_map.py` は実験の `fold` の結果を読んでセルの状態と照合できる。

## 8. 段階的な導入

1. **最小の版:** `upcast`（`v` を最初から入れる。後から足すと既存の出来事の移行が要る）、`fold`、`next_step`、`check`、`te add`・`te next`・`te check`・`te brief`・`te source add`。
2. **試す:** 既存の記録1本を移し（12章の試しを新しい欄でやり直す）、`te check` が既知の失敗（藁人形、自己攻撃、確認済みの根拠の欠落、孫引き）を検出するかを確かめる。
3. **評価:** 評価ケースを複数回走らせ、`te next` が呼ばれる割合と、価値の確認と独立した攻撃が行われる割合を、散文版と比べる。
4. その後に `te run`、`te render`（Argdown を含む）。

## 9. 決めたことと、決めていないこと

決めたこと（11章の調査に基づく）:

- 出来事の列は JSON Lines（追記が1行で済み、git の差分で1出来事が1行に見え、壊れた末尾行を検出でき、`jq` で扱える）。
- 長い自由記述は `notes/<id>.md` に分ける。
- 既存の記録は移さず、新しい実験から te を使う。評価用に1本だけ一回限りで移す（Overeem ら 2021 は copy-and-transform を性能か保守性が落ちたときに限る）。
- 正本にしない標準: RO-Crate、CloudEvents の外枠、PROV-O、AIF。対応表か片方向の書き出しにとどめる。

レビューで決めたこと（ユーザーの判断）:

- **CI での `te.py` の入手:** プラグインの固定したコミットを取得し、使った版を記録する。利用者のリポジトリの根に `te.lock`（プラグインのリポジトリの URL、コミット、`te.py` の sha256）を置く。CI はそのコミットを取得して sha256 を照合してから実行し、`te check` は使った版（コミットと sha256）を出力の先頭に書く。版を上げるときは `te.lock` を書き換えるコミットにする。
- **予想の採点:** 出す。`score`（4章）が Brier スコアを計算し、`te render` が README に載せ、`te next` は結論の後に表示する。採点は事後評価（`review`）の「驚き」の材料にする。採った仮説に置いた確率が低いほど、結果は事前の予想から離れていた。

決めないこと:

- **MCP サーバーへの移行:** 起きてから考えれば間に合う（ユーザーの判断）。`te next` が呼ばれないことが評価で分かったときに検討する。いまは設計に含めない。

## 10. 外部の標準との対応（要約）

| te の要素 | 由来 |
| --- | --- |
| 出来事の列、`v` と `upcast`、訂正を新しい出来事にする | Event Sourcing（Fowler）、Overeem ら 2021、Greg Young |
| `objections.target` | ASPIC+（undermine / rebut / undercut） |
| `rival.would_reject_if` | 敵対的共同研究（反証の条件を事前に合意する） |
| `prediction.distribution`、`reference_class` | Good Judgment Project の採点と訓練（Mellers ら 2014、Chang ら 2016） |
| `accepted_downsides`、`supersede` | Nygard の ADR、MADR 4.0.0 の Consequences、Y-statement |
| `if_false` | ICD 203（要となる仮定と、それが誤っていたときの影響） |
| `citations.level`、`primary_of`、`role` | W3C PROV-O（hadPrimarySource）、CiTO |
| 生き残りの計算 | Carneades の proof standard |
| `--argdown` | Argdown（MIT） |

出典と、一次資料での確認の結果は、ryo-morimoto/thought-experiments の `reports/思考実験の標準構造と先行事例.md` と `research_notes/思考実験の標準構造と先行事例/` にある。

## 11. 調査の結論（要約）

- te の骨格は、Event Sourcing、ADR、ACH、IBIS、英国防省の Red Teaming Handbook などと独立に一致する。形式を取り込む必要は小さく、取り込むのは欠けている概念（10章）。
- ACH の点数付けや、仮説の自動順位付けは取り込まない。分析官を対象にした実験（Dhami ら 2019、Mandel ら 2018）で、確証バイアスの軽減ははっきりせず、判断の不整合を増やしうると報告されている。
- 「文脈を持たない reviewer は自己攻撃より良い」は、外部の実証のない仮説として扱う。いまの根拠は、このプラグインの評価ケース（#29）だけ。

## 12. 既存の記録で試した結果（第1版の欠陥）

ryo-morimoto/thought-experiments の `experiments/2026-11-21-life-value-in-flood-bc.md` を、第1版の形式で23件の出来事に移し、規則を試した。

- **入らなかったもの:** 問いの範囲の変更（第1版は問いを不変の身元に置いていた）、仮説の状態の度合い（二値しかなかった）、事後評価と価値の評価、一回限りの計算の表、実務者向けの主張と分岐元。第2版で `frame.supersedes`、`verdicts`、`review`、`outputs/` の運用、`conclusion.claim`、`branch.from` を足した。
- **欄名の衝突:** 共通の `by` と攻撃の `by` がぶつかっていた。`author` と `reviewer` に分けた。
- **規則の試し:** 5本中3本が違反を出したが、既知の失敗4つのうち確実に止まるのは2つだった。「調べた」「文脈を持たない reviewer が攻撃した」は書けば通り、藁人形は別の仮説に保持者がいれば通り、孫引きは一次資料を経由していれば通った。第2版で、生成物による証明（2.2）、`holder(attacked_rivals)`、組ごとの一次・二次と `primary_of` の追跡（2.3）に直した。
- **一次資料で確かめ直すと:** 記録が使っていた事実のうち、人命の値（技術指針の精神的損害額だけで、総額ではなかった）、Kawabata ら（2023）の対象期間、Knutson ら（2019）が弱い基準を使った理由の3つが誤っていた。どれも孫引きが原因だった。

## 13. 実装（第1版）で設計から変えたこと

8章の1と4を一度に入れた。設計と違う点:

- **コマンドを足した:** `te init`、`te score`、`te version [--verify]`、`te lock`、`te render --write / --reply / --lang ja`、`te next --all`（全段階の不足を一度に出す。既存の記録の監査用）。
- **段階D（事後評価と閉じる）を足した:** `review` と `close` を `requires` にした。予想の採点は段階C の後に `te next` が表示する。
- **藁人形の検査を不変条件に移した:** 段階A は `holder` があることだけを求め、`eliminate-needs-holder` が「弱めた・脱落させた仮説には、取得済みの出典を持つ holder か、藁人形の印が要る」を常に検査する。攻撃の対象が決まるのは段階B 以降なので、段階A の `requires` では判定できない。
- **不変条件を足した:** `refs-exist`（仮説・出来事・出典・ファイルの参照先がある）、`prediction-sums-to-one`、`answer-rival-survives`（脱落した仮説を結論に採らない）、`artifacts-match`（依頼文と応答の sha256）。警告に `strawman`、`quotes-verified`、`self-attack`、`operation-secondhand` を足した。`operation-secondhand` は、probe と operation の `sources` に引用（`{source, level, primary_of}`）も書けるようにしたうえで、一次資料を取得していない二次資料を操作に使ったときに警告する（下の試しで見つけた穴）。
- **自己攻撃の扱い:** subagent を使えない環境のために、利用者が `decision`（`author = "user"`、`accepts = <attack の id>`）で認めた自己攻撃だけ段階C を通す。Claude の decision では通らない。
- **訂正:** `correction.replace` が対象の出来事に新しい値を重ねる。元の行は書き換えない。
- **`te.lock`:** te を複数のファイル（`te.py`、`telib/`、`data/`）に分けたので、`te.py` の sha256 ではなく、それらをまとめた `bundle_sha256` を記録する。
- **スキーマの検査:** 標準ライブラリだけで、v1 のスキーマが使うキーワードに絞った検査器を書いた。知らないキーワードがあれば例外にし、黙って通さない。
- **`check_limits.py`:** `scripts/` と `data/` は読まれず実行されるので、ファイルの文字数の上限から外し、te が表示する文（指示 600、lens 400、規則の文 300、1段階で表示する指示の合計 1600）に上限を置いた。

### 8章の2 の試し：人命の記録を v1 に移す

12章の写像（ryo-morimoto/thought-experiments の `experiments/2026-11-21-life-value-in-flood-bc.md` を出来事に写したもの）を、欠けている欄を作らずに v1 へ移した（記録にない必須欄には「移行で補った印」を入れ、どこに入れたかを一覧にした）。`te next --all` と `te check --no-rerun` の結果:

| 既知の失敗 | 検出 | どこで |
| --- | --- | --- |
| 先行する答えを探していない | した | 段階A `prior_answer_evidence` |
| 予想を書いていない | した | 段階A（予想がないので採点もできない） |
| 藁人形（L5 を脱落させたが、誰の立場かを示していない） | した | 不変条件 `eliminate-needs-holder`（ERROR） |
| 自己攻撃 | した | 段階C、警告 `self-attack` |
| 反論への応答に区分がない（自由記述だけ） | した | 段階C `objections_answered`（5件） |
| 孫引き（取得していない技術指針 R6 の値を、砂防の資料経由で操作2と操作5に使った） | 最初はしなかった。前提の引用しか見ていなかったため。`operation-secondhand` を足して検出 | 警告 |
| 棄却の条件を先に書いていない | スキーマが必須にしているので、移行の時点で欠落として一覧に出た | スキーマ |
| 結論の数値の出どころ（前提が `outputs/` ではなく計算のスクリプトを指す） | 移行の時点で一覧に出た | スキーマ（`outputs/` だけを許す） |

まだしていないこと: 8章の3（散文版との比較評価）。`te render` は `outputs/` の数値を本文に埋め込まず、前提の `outputs` 欄で参照する。
