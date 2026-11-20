---
name: draft-review-comments
description: PR のレビューコメントの下書きを作る。レビューコメントを書く、気づきを整理してコメントにする、レビューの論点に優先づけの案を出す、とき。Draft review comments for a pull request. Use when asked to write review comments, turn findings into review comments, or prepare comments for approval before posting.
---

# レビューコメントの下書きを作る

気づきを集め、優先づけの案を出し、下書きを作り、独立した確認を経て、承認できる状態にするところまでを扱います。

**決めるのは人です。** 優先づけ、承認は、人が決めます。この skill は、下準備、下書き、確認を担います。

記録の書式は `references/records.md`、書き方の基準は `references/rules.md`、気づきの取り込み方は `references/intake.md` にあります。スクリプトは、`SKILL.md` があるディレクトリ（以下 `<skill>`）の `scripts/` にあります。`<skill>` は、skill の読み込み時に示される基底ディレクトリです。示されないときは、`find` で `skills/draft-review-comments/SKILL.md` を探します。コマンドは、どの作業ディレクトリからでも動くように、`<skill>/scripts/…` の絶対パスで書きます。

## 手順

### 0. 問いと動機を確認する

何を知りたいのか、何のためなのかを、1 行で確認します。規則に関わる指摘かどうかも、聞きます。決めつけず、利用者に確かめます。

### 1. 気づきを取り込む

`references/intake.md` に従います。pr-tour の JSON なら、`<skill>/scripts/import-findings.py` で取り込みます（`--repo` に対象のリポジトリを渡し、先に `--dry-run`）。

記録の置き場所（`--store`）は、XDG の仕様に従い、`${XDG_DATA_HOME:-$HOME/.local/share}/pr-review` を使います。

### 2. 事実を集める

気づきの根拠になる事実を集めます。コードへの固定リンク（`blob/<40 桁の SHA>/…`）を引用するときは、`scripts/resolve-permalinks.py` で確かめます。

```
python3 <skill>/scripts/resolve-permalinks.py --repo <リポジトリのパス> [--expect <owner/repo>] <下書きのファイル>
```

- 確かめられるのは、**行が存在すること、その本文**だけです。リンクが主張に関係しているかは、確かめられません。人が読んで判断します。
- 推論は「推論」、確認できていないことは「未確認」と書きます。

### 3. 優先づけの案を出す

**決めるのは人です。** 気づきごとに、次の案を出して、人に見せます。

- `action`: `share`（認識共有のみ）、`ask`（意見を聞きたい）、`analyze`（分析をお願いしたい）、`change`（対応をお願いしたい）
- `blocking`: マージを止めるか
- `importance`: `high`、`mid`、`low`

気づきごとに、「読む人に決めてほしいこと」と「扱う場所（この PR か、別の issue か）」が書けるかを確かめます。書けなければ、コメントにしない案を、人に示します（`references/rules.md` の「コメントにする条件」）。

人が決めたら、assessment を記録します。

- `intent_quote`（何を実現したいか）と `premise_quote`（そう考える前提）は、**人の言葉の原文**を、言い換えずに書きます。
- 人が言葉にしていなければ、書かずに、聞きます。
- 却下するときは、気づきの `dismissed_reason` に、人の言葉の原文を 1 回だけ書きます（`references/records.md` の記入例）。

### 4. 下書きを作る

`references/rules.md` の 3 部形式で書きます。**1 つの指摘を、1 つのコメントにします。** draft と rev-001 を記録します。コメント本文に引用する固定リンクは、rev-001 の `references` にも書きます。

### 5. 確認する

1. `resolve-permalinks.py` を、下書きに通します。結果を見ます。
2. `evaluator`（独立した確認役）を呼びます。渡すのは、**下書きのパス、`rules.md` のパス、`resolve-permalinks.py` のパス、リポジトリのパス**（すべて絶対パス）だけです。自分の結論や、直したい点は渡しません。呼べないときは、`evaluator.md` の手順に従って自分で評価し、独立した確認ではないと、人に伝えます。
3. 確認役の指摘は、**根拠になっているか、関連しているかを、自分で確かめてから**取り込みます。
4. 取り込むときは、新しい版（rev-002 以降）にします。`reason_quote` に、人の言葉を書きます。

### 6. 承認を求める

下書きを人に見せ、承認を求めます。複数の点に違和感があり、承認か差し戻しかを一度に決めにくいときは、文や語句ごとにコメントしてもらいます。

```
python3 <skill>/scripts/render-review-html.py <下書きの Markdown> --out <HTML のパス>
```

作った HTML を開き、文にカーソルを合わせて 💬 を押すか、語句を選んでコメントします。「Copy for AI」で、コメントを Markdown として書き出せるので、それを受け取って新しい版（rev-002 以降）を作ります。HTML には下書きの内容が入るので、公開の場所には置きません。

人が承認したら、その版の `approved_by` と `approved_at` を埋めます。**承認されていない版は、投稿に進みません。** 版は、承認の 2 つの欄を `null` で作り、承認されたら、2 つを同時に書き込みます。

### 7. 記録を検査する

```
python3 <skill>/scripts/validate-records.py --store "${XDG_DATA_HOME:-$HOME/.local/share}/pr-review"
```

書式に合わない点があれば、直します。

## この skill は投稿しない

この skill は、GitHub に投稿しません。投稿は、承認のあとに人が行います。投稿したら、`references/records.md` の posting の記録を残します。

## 迷ったとき

- 断定しません。
- 事実と推論を分けます。
- わからないことは、「未確認」と書きます。
- 人の判断が要る点は、人に返します。
