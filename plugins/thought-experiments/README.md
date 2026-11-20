# thought-experiments

> **検証中（experimental）です。** より良いスコープに組み替える可能性が高く、名前・構成・地図の書式は、予告なく変わります。

## 目的

思考実験を、問いの設定から結果への攻撃まで、人と一緒に回します。1 回の実験で終わらせず、結論を「地図」に書き戻して、どこまで分かっていて、次にどこを考えるべきかを見えるようにします。

地図の軸には、なるべく既存の標準や論文の分類を使います。自作の分類は、自分が思いつかなかった値を見落とすためです。

**どこを考えるか、どの信念を手放すかは、人が決めます。** エージェントは、選択肢を広げ、条件を変えて試し、結果を攻撃し、記録を保ちます。

## インストール

```
/plugin install thought-experiments --marketplace ryo-morimoto/plugins
```

この行は `claude plugin validate` が示した形で、インストールそのものは試していません。

## 構成

| 部品 | 種類 | 内容 |
| --- | --- | --- |
| `running-thought-experiments` | skill | 1 回の思考実験の手順。問いと用語の定義 → モードの選択 → 対立する案 → 条件を変える操作 → 結果への攻撃（英語で書かれ、利用者の言語で応答する） |
| `mapping-thought-experiments` | skill | 複数の実験をまたぐ地図を作り、次の候補を出して選んでもらい、結論を書き戻す |
| `thought_map.py` | script | 地図の検査、候補（frontier）の算出、`map.html` の生成 |
| `map_page.py` | script | `map.html` の見た目。外部の読み込みはしない |
| `assets/map.toml`、`assets/experiment.md` | 雛形 | 地図と、実験の記録 |

`mapping-thought-experiments` は、実験の手順を `running-thought-experiments` に任せます。無くても動きますが、手順は簡略になります。

## 地図

利用者のリポジトリの `maps/<name>/map.toml` に書き、`map.html` を生成します。`map.html` をブラウザで開くと、次のことができます。

- セルの状態を色と模様で見る（結論は塗り、仮説は斜線、未探索は破線の空白）
- 次の候補を順位つきで見る。選ぶと、推論の前提になるセルが光る
- 候補を Claude Code に渡すコマンド（`/thought-experiments:mapping-thought-experiments maps/<name> <row>/<col>`）をコピーする

```sh
python3 <skill>/scripts/thought_map.py frontier maps/<name>   # 次の候補
python3 <skill>/scripts/thought_map.py render                 # map.html を生成
python3 <skill>/scripts/thought_map.py check                  # 形式と map.html の鮮度（CI 向け）
```

依存は Python 3.11 以上の標準ライブラリだけです。テスト: `python3 -m unittest discover -s plugins/thought-experiments/tests`

## 対応するツールと、ファイルの形

| ファイル | 形 | 内容 |
| --- | --- | --- |
| `plugin.json`（plugin の根） | Agent Plugins 1.0 | 標準の manifest |
| `skills/*/` | Agent Skills | skill。スクリプト・参照・雛形を含む |
| `.claude-plugin/plugin.json` | Claude Code | Claude Code の manifest（根の `plugin.json` とは別の形式） |

動作を確認しているのは、Claude Code だけです。

## 構成の判断

この形は、2026-11-21 に、構成そのものを題材にした思考実験（上限 30 分）で選びました。

| 案 | 結果 | 理由 |
| --- | --- | --- |
| 1 つの plugin に 2 つの skill | **採用** | 依存が片方向で弱く、一緒に入っているほうが劣化しない。使わない skill の負担は説明文 1 つ分 |
| plugin を 2 つに分ける | 保留 | 地図だけ、実験だけを使う 2 つ目の使い手は、まだいない |
| 1 つの skill に統合する | 不採用 | 時間の尺度が違う（1 セッションと、複数セッション）。実験の skill は読み込みを小さく保つ制限を持ち、地図の重さを毎回読ませたくない。代わりに、実験の状態から地図のセルへの対応を `mapping-thought-experiments` に明記した |
| さらに分解する（描画、軸の探し方を独立） | 不採用 | 2 つ目の使い手がいない（原則 5） |
| 地図は公開しない | 不採用 | 公開すること自体が、元のリポジトリ以外での利用を作る。そのため、元のリポジトリ固有の前提（データ利用ポリシーの検査など）を外した |

見直す条件:

- 地図の描画や検査を、思考実験以外（設計の比較、調査の網羅など）で使いたくなったら、地図を独立させる。
- `mapping-thought-experiments` が、ふつうの思考実験の依頼で誤って起動したら、説明文を絞るか、plugin を分ける。

## 未確認のこと

- skill の自動起動（質問から自動で選ばれるか）と、2 つの skill の間で取り違えが起きないか。
- `map.html` の「コピー」が渡すコマンドの形（`<plugin>:<skill>` と引数）で、Claude Code が skill を呼べるか。
- 根の `plugin.json` が標準の schema に合うか（機械的には検証していない）。
