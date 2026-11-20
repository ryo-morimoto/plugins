---
name: mapping-thought-experiments
description: 複数の思考実験をまたいで、問いの空間を2軸の地図（maps/<name>/map.toml と map.html）にし、標準や論文の分類を軸に、空いているセルと次に推論すべき方向を出して、利用者に選んでもらいながら1セルずつ埋める。「地図」「次どこを考える」「空いているところ」「思考実験を続ける」と言われたとき、または map.html からコピーしたコマンドで呼ばれたときに使う。単発の思考実験は running-thought-experiments を使う。Map a question space across many thought experiments and pick the next cell to explore.
---

# 思考実験の地図を埋める

地図は「2つの軸で区切った問いの空間」。1回のループで1セルだけ動かす。結論は利用者と一緒に出し、根拠のない結論は書かない。

スクリプトは、この `SKILL.md` があるディレクトリ（以下 `<skill>`）の `scripts/` にある。`<skill>` は読み込み時に示される基底ディレクトリで、示されないときは `find` で `skills/mapping-thought-experiments/SKILL.md` を探す。地図は利用者のリポジトリの `maps/<name>/` に置き、コマンドはそのリポジトリの根で実行する（違う場所なら `--root`）。

- 書式・状態・候補の出し方: `references/map-format.md`
- 軸の選び方（標準・論文の分類を探す）: `references/choosing-axes.md`

## 0. 地図を選ぶ・作る

既存の地図は `ls maps/`。合う地図がなければ `<skill>/assets/map.toml` を `maps/<name>/map.toml` にコピーし、問いを1文にしてから、`references/choosing-axes.md` に従って軸を決める。軸の候補は出典つきで2〜3個示し、利用者に選んでもらう。

## 1. 候補を出して選んでもらう

引数に `maps/<name> <row>/<col>`（または `axis:rows` / `axis:cols`）があれば、map.html からコピーされた指定なので、選択を飛ばして 2 に進む。理由とモードは `frontier --json` の該当項目を使う。

引数がなければ:

```sh
python3 <skill>/scripts/thought_map.py frontier maps/<name> --top 6
```

上位3つを選択肢にして聞く（4つ目は「地図全体を見る」）。各選択肢には、セル名・状態・モードと、**なぜそこか**（どの隣のセルの結論から推論するか）を1〜2文で書く。`maps/<name>/map.html` をブラウザで開けば、全体と前提のセルが見えることも伝える。利用者が別のセルや新しい軸を言ったら、それに従う。

## 2. 思考実験を回す

`running-thought-experiments` が使えるなら、それに従う。行と列の値の定義（map.toml の `note`）を、前提として最初に示す。使えないときも、問い → 対立する案を3つ以上 → 条件を1つずつ変える → 結果を攻撃する、の順は守る。

記録は `experiments/YYYY-MM-DD-<slug>.md` に書く（雛形: `<skill>/assets/experiment.md`）。

## 3. 地図に書き戻す

running-thought-experiments の状態（State）を、セルにこう移す。

| 状態の欄 | セルの欄 |
| --- | --- |
| 生き残った結論と、その前提 | `claim`（1〜3文） |
| Results で裏付けあり / Eliminated で仮説が否定 | `status = "supported"` / `"refuted"` |
| 結論が Unverified の前提に依存 | `status = "hypothesis"` |
| 対立する案が両方残った | `status = "contested"` |
| 読んだ出典と実験の記録 | `evidence` |
| Mode / Next moves | `mode` / `next_question` |

ほかのセルに効く結論が出たら、そのセルに `open` を置く。軸に足りない値が見つかったら、利用者に確認してから足す。

```sh
python3 <skill>/scripts/thought_map.py render maps/<name>
python3 <skill>/scripts/thought_map.py check
```

最後に、変わったセル・埋まり具合・次の候補の上位3つを短く報告して、続けるか聞く。
