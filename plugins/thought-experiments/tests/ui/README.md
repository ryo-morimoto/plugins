# 地図の画面の検査（veriss）

`map.html` を、[mizchi/veriss](https://github.com/mizchi/veriss)（描画せずに、CSS と DOM から、全画面幅のレイアウト・アクセシビリティ・CSS の誤りを検査する）にかけます。文字の幅と高さは、veriss がフォントファイルから導きます（[ADR-0010](https://github.com/mizchi/veriss/blob/main/docs/adr/0010-font-derived-text-metrics.md)）。

```sh
python3 ../../skills/mapping-thought-experiments/scripts/thought_map.py --root fixture render fixture/maps/all-states

VERISS=<veriss の clone>/packages/veriss \
FONT_JP=<NotoSansJP[wght].ttf> FONT_MONO=<NotoSansMono[wdth,wght].ttf> \
CHROME=<Chromium> \
BLOCK=0 ALLOW=U_A11Y_TARGET_SIZE node check.mjs      # 横方向だけ（数分）
```

`fixture/maps/all-states/`（7 つの状態と、軸の札の組み合わせをすべて含む地図）を、3 つの状態 × 4 つの部品 × 4 つの幅の帯、計 48 通り検査します。終了コードは、`ALLOW` にない指摘が 1 つでもあれば 1 です。

## 2 つのモード

| モード | 指定 | かかる時間 | 結果 |
| --- | --- | --- | --- |
| 横方向だけ | `BLOCK=0` | 数分 | ヘッダーと軸の札は `verified`。地図の表と候補の欄は、押せる範囲の大きさ（縦方向が要る）だけが判定不能 |
| 縦方向も | 既定 | 数時間以上 | 押せる範囲の大きさも決まる。幅の帯は、作業量の上限に当たるたびに半分にして検査し直す |

縦方向の検査は重く、アクセシビリティ（`A11Y=core` で軽くなる）と、スクロールバーの太さの宣言（`SCROLLBARS=overlay`）が主な原因です。一部だけ回すには `STATES=1,4,5`、`PARTS=header,axes,grid,cands`、`BANDS=320-399`、`RANGES=320,600` を使います。

## 準備

- veriss は npm に公開されていません。`git clone https://github.com/mizchi/veriss` し、`pnpm install --ignore-scripts` します。確かめたのは commit `28c561f` です。veriss には、この時点で LICENSE がありません（手元での検査にだけ使い、このリポジトリには含めません）。
- フォントは Google Fonts の Noto Sans JP と Noto Sans Mono（OFL）。ページの `font-family` の先頭と一致させます。
- Playwright は veriss の依存にあるものを使います。版が求める Chromium がなければ、`CHROME` で手元の Chromium を指定します。
- **veriss の不具合への手当てが要ります。** 押せる範囲の大きさ（target-size）の検査は、縦方向の大きさがわからない箱（横方向だけのとき、すべての箱）で `TypeError` を出して止まります（`src/layout/accessibility.mjs` の `undersized`）。手元では、その対象を「判定不能」に回し、隣の対象は「どこでも小さいかもしれない」とみなすように直しました。

## 検査のしかた（`check.mjs`）

1. Playwright で描画し、文字を持つ箱ごとに、計算済みのフォント（family の先頭、px の大きさと行の高さ、太さ）、表示される文字列、`white-space` を集めて id を付ける。
2. `<script>` を除き、`style` 属性は id の規則に移し、`<code>` は表示の同じ `<span>` にする（veriss の HTML の読み込みが `code` を扱わないため）。
3. 部品（ヘッダー、軸の札、地図の表、候補の欄）に分ける。`main` の列の幅は中身に依存せず、地図の欄の中は縦に並べているだけなので、分けても各部品の幅は変わらない。
4. 文字の箱ごとに `text` 契約（文字列とフォント）を作る。折り返す箱は行分割のモデルで、折り返さないラベル（`white-space: nowrap`）は 1 行の幅で測る。行分割のモデルが扱わない文字（記号の一部、隣り合う全角の約物など）を含む箱は、1 行に収まることを要求して測り、収まらない幅は veriss が誤りにする。それも測れない箱は「測れなかった」として失敗にする。

## ページ側で守ること

veriss が判定できる書き方の条件です。`map.html` のテンプレートはこれを守っています。

- フォントは `font-family` / `font-size`（px）/ `line-height`（数値か px）/ `font-weight` で書き、`font` の省略形と `letter-spacing` を使わない。見出しの太さも明示する。
- `line-height` は、使う文字の大きさとの積が 2 進で割り切れる値にする（1.5 など）。1.6 だと、veriss が導いた高さが自分の入力検査に落ちる（veriss の不具合）。
- 文字を横に並べるときは flex ではなく、列を明示した grid にする。行をまたぐ配置（`grid-row: span`）、ベースラインでの揃え、`justify-self` は使わない。
- 高さを指定しない（`height` / `min-height`）。色の帯や丸は、枠線の太さや行の高さで大きさを決める。点線は `outline` で描く。
- フォントにない文字（例: `✕`）を使わない。生成する文の中で、全角の約物を隣り合わせない（例: `。」`）。
- ブラウザ既定の余白（`p` など）は明示する。

## わかっている限界

- 縦方向の検査は、地図の表で「Ambiguous layout contracts」のエラーになる（同じ見出しは、軸の札の部品では通る。原因は未特定で、veriss の不具合の可能性がある）。候補の欄は、1px の帯まで分けても作業量の上限を超える箇所が残る。
- 地図の中身（結論や行の名前）に、行分割のモデルが扱わない文字（`①`、`。」` など）があると、その箱は 1 行の幅で測られ、狭い幅では誤りになる。
- 検証はフォントが Noto Sans JP で描かれることが前提。Noto Sans CJK JP が入っている環境では、そちらで描かれる（字幅は同じ設計だが、一致は確かめていない）。
