# 記録の書式（段階 1）

`pr-review` が残す記録の形です。普通のテキストだけで読み書きでき、置き場所（ローカル、共有の場所）を移せます。

## 原則

- **1 件の記録を 1 つのファイルにする。** 書き手が複数になっても、ファイルが衝突しない。
- **一次の記録は、作成後に書き換えない。** 原文、固定リンク、人の言葉を、そのまま残す。例外は「後から埋める欄」だけ（下の表）。
- **要約や言い換えを、一次の欄に保存しない。** 言い換えは、作り直せるキャッシュとして別に持ち、判断の根拠にしない。
- **計算できる値は保存しない。** 気づきの状態（未処理・判断済み・下書き中・投稿済み）などは、他の記録の有無から出す。
- **削除しない。** 取り下げや却下は、日時と理由の記録で表す。

## ファイルの形

先頭に front matter、そのあとに本文を置きます。

```
---
type: finding
schema: 1
id: "20261120T060500Z-3fa9c1"
title: "..."
---
本文（原文のまま）
```

- front matter は、`---` だけの行で囲む。
- **1 つのキーを 1 行に書く。** `キー: 値`。値は JSON で書ける型だけを使う（文字列は二重引用符、数値、`true`／`false`、`null`、配列、オブジェクト）。複数行の値は使わない。
- 長い文章は、本文に書く。
- すべての記録に `type`（種類）と `schema`（書式の版。今は `1`）を付ける。

## id

- 通常の id: `<UTC の yyyymmddThhmmssZ>-<16 進 6 桁>`。例 `20261120T060500Z-3fa9c1`。時刻順に並び、衝突しにくい。
- PR の id: `owner/repo#番号`。
- スナップショットの id: `owner/repo#番号@<head の先頭 7 文字>`。

## 配置

```
<store>/pulls/<owner>/<repo>/<番号>/
  pull.md
  snapshots/<head7>.md
  findings/<finding-id>/
    finding.md
    assessments/<id>.md
    drafts/<draft-id>/
      draft.md
      rev-001.md  rev-002.md …
      postings/<id>.md
```

`<store>` は、利用者が決める置き場所の根です。推奨は、XDG の仕様に従った `${XDG_DATA_HOME:-$HOME/.local/share}/pr-review` です。公開リポジトリには、入れません。ファイルの中身と、この配置の相対パスだけが約束で、絶対パスは書きません。

## 種類ごとの項目

型の欄の `?` は、`null` を許す項目です。

### pull（`pull.md`）

| 項目 | 型 | 意味 |
| --- | --- | --- |
| `id` | 文字列 | `owner/repo#番号` |
| `url` | 文字列 | PR の URL |
| `series` | 文字列? | 同じ取り組みのまとまり（例 `EX-1`） |
| `title` | 文字列? | キャッシュ。GitHub が正 |
| `author` | 文字列? | キャッシュ。GitHub が正 |
| `fetched_at` | 文字列 | キャッシュを取得した UTC 時刻（ISO 8601） |

### snapshot（`snapshots/<head7>.md`）

| 項目 | 型 | 意味 |
| --- | --- | --- |
| `id` | 文字列 | `owner/repo#番号@<head7>` |
| `pull_id` | 文字列 | pull の id |
| `head_sha` | 文字列 | 40 桁の 16 進 |
| `base_sha` | 文字列? | 40 桁の 16 進 |
| `fetched_at` | 文字列 | UTC 時刻 |

### finding（`findings/<id>/finding.md`）

本文は、**気づきの原文**です。

| 項目 | 型 | 意味 |
| --- | --- | --- |
| `id` | 文字列 | |
| `pull_id`、`snapshot_id` | 文字列 | 作った時点のスナップショットに固定する |
| `run_id` | 文字列? | 段階 1 では常に `null` |
| `origin` | `"human"` か `"detector"` | |
| `origin_ref` | 文字列? | 元のコメントの ID、または検出の出力の識別子 |
| `title` | 文字列 | 原文の先頭の 1 行（長ければ 120 文字で切る） |
| `body_hash` | 文字列 | 本文の SHA-256（16 進）。本文は、前後の `\n` を除いた UTF-8（`\r` は除かない）。書き換えの検知に使う |
| `location` | オブジェクト? | `{"path": …, "start_line": 整数, "end_line": 整数, "side": "left"か"right"}` |
| `confidence` | `"confirmed"`、`"plausible"`、`"unknown"` | |
| `theme_key` | 文字列? | 複数の PR にまたがる話題のラベル |
| `norm_gap` | `null`、`"missing"`、`"unclear"`、`"violated"`、`"conflicting"` | 規則が無い・曖昧・破られている・矛盾している、のどれか |
| `norm_ref` | 文字列? | データの外にある規則や ADR への URL や ID |
| `dismissed_reason` | 文字列? | **後から埋める欄**。人の言葉の原文 |
| `created_by`、`created_at` | 文字列 | `created_by` は GitHub のログイン名、または `agent:<名前>` |

### assessment（`assessments/<id>.md`）

人の判断の記録です。本文は使いません。

| 項目 | 型 | 意味 |
| --- | --- | --- |
| `id`、`finding_id` | 文字列 | `finding_id` は、親のフォルダの finding と一致する |
| `profile_id` | 文字列? | 段階 1 では常に `null` |
| `action` | `"share"`、`"ask"`、`"analyze"`、`"change"` | 認識共有のみ／意見を聞いて重要度を判断／分析をお願い／対応をお願い |
| `blocking` | 真偽値 | |
| `importance` | `"high"`、`"mid"`、`"low"` | 段階 1 では、人が決める |
| `intent_quote` | 文字列 | 何を実現したいか。**判断した人の言葉の原文** |
| `premise_quote` | 文字列? | そう考える前提や見込み。判断した人の言葉の原文 |
| `rationale_ref` | 文字列? | その言葉が出た場所（会話の識別子、コメントの URL など） |
| `assessed_by`、`assessed_at` | 文字列 | |

### draft（`drafts/<draft-id>/draft.md`）

| 項目 | 型 | 意味 |
| --- | --- | --- |
| `id` | 文字列 | |
| `assessment_id` | 文字列 | |
| `withdrawn_at` | 文字列? | **後から埋める欄** |

### revision（`drafts/<draft-id>/rev-NNN.md`）

本文は、**下書きの本文**です。版ごとに別のファイルにして、あとから直さず、新しい版を足します。

| 項目 | 型 | 意味 |
| --- | --- | --- |
| `draft_id` | 文字列 | |
| `rev` | 整数 | 1 から連続する。ファイル名の `NNN`（3 桁）と一致する |
| `references` | 配列 | 引用した参照。`[{"kind": "repo", "url": 固定リンク}, {"kind": "external", "url": …, "reading": "full"か"summary"か"unverified"}]` |
| `changed_by`、`changed_at` | 文字列 | |
| `reason_quote` | 文字列? | 直した理由。人の言葉の原文。第 1 版は `null` |
| `approved_by`、`approved_at` | 文字列? | **後から埋める欄**。2 つとも埋めるか、2 つとも `null` |

### posting（`drafts/<draft-id>/postings/<id>.md`）

外部（GitHub）への投稿の記録です。本文は使いません。

| 項目 | 型 | 意味 |
| --- | --- | --- |
| `id`、`draft_id` | 文字列 | |
| `rev` | 整数 | 投稿した版 |
| `mode` | `"new"`、`"edit"` | |
| `github_comment_id` | 文字列 | |
| `url` | 文字列 | |
| `payload_hash` | 文字列 | 送った本文の SHA-256（16 進） |
| `anchor_verified` | 真偽値 | 投稿後に、位置を取得して確かめたか |
| `head_sha_at_post` | 文字列 | 40 桁の 16 進 |
| `posted_at` | 文字列 | |
| `outcome` | `"pending"`、`"aligned"`、`"changed"`、`"disagreed"`、`"dropped"` | **後から埋める欄**。人が判断する |
| `reply_refs` | 配列 | **後から追記する欄**。GitHub の返信の ID |
| `outcome_judged_by` | 文字列? | `outcome` を `pending` 以外にしたときだけ埋める |

## 後から埋める欄

不変の原則の、明示した例外です。

| 欄 | ルール |
| --- | --- |
| `finding.dismissed_reason` | `null` から文字列へ、1 回だけ |
| `draft.withdrawn_at` | 同上 |
| `revision.approved_by`／`approved_at` | 2 つ同時に、`null` から値へ、1 回だけ |
| `posting.outcome`／`outcome_judged_by` | `pending` から別の値へ、1 回だけ |
| `posting.reply_refs` | 追記だけ。既存の要素を消さず、書き換えない |

この例外が、事象として別のファイルにするより緩い選択であることは、設計上の未解決点です（README の「現状と制限」を参照）。

## 検査（`validate-records.py` が確認すること）

1. 必須項目があり、型と列挙値が正しい。未知の項目も、段階 1 で常に `null` の欄（`run_id`、`profile_id`）が `null` でない場合も、誤りとする。
2. `type` が、この版で対応する種類である（段階 2 以降の種類は、未対応として報告する）。
3. ファイルの位置が、id と一致する（PR のフォルダは `pull.id`、finding のフォルダは `finding.id` など）。
4. 参照先が存在する（`pull_id`、`snapshot_id`、`finding_id`、`assessment_id`、`draft_id`）。
5. finding の `body_hash` が、本文の SHA-256 と一致する。
6. revision の `rev` が、1 から連続し、ファイル名と一致する。
7. revision の `approved_by` と `approved_at` が、両方埋まるか、両方 `null`。
8. posting の `rev` が存在し、**その版が承認済み**である。
9. 同じ（draft, rev, mode）の posting は、1 つだけ。
10. `location` の `start_line` が `end_line` 以下で、1 以上。
11. revision の `references` のうち `kind: "repo"` の URL が、40 桁の SHA に固定された blob の固定リンクである。
12. `posting.outcome` が `pending` 以外なら `outcome_judged_by` が埋まっている。

## 記入例

検査を通った例です（架空のデータ）。

- `type` の値: `pull`、`snapshot`、`finding`、`assessment`、`draft`、`revision`、`posting`。
- id: `echo "$(date -u +%Y%m%dT%H%M%SZ)-$(openssl rand -hex 3)"`。
- 時刻: `date -u +%Y-%m-%dT%H:%M:%SZ`。
- ハッシュ: `printf '%s' "<本文>" | shasum -a 256`。`payload_hash` は、投稿した本文（rev の本文の、前後の `\n` を除いたもの）に、`body_hash` と同じ規則で出す。検査は、中身の一致までは見ない。
- 承認: 版は、`approved_by` と `approved_at` を `null` で作り、承認されたら、2 つを同時に書き込む。
- 却下: 気づきの `dismissed_reason` に、人の言葉の原文を 1 回だけ書く。

### assessment

```
---
type: "assessment"
schema: 1
id: "20261120T074333Z-02600c"
finding_id: "20261120T074322Z-3b9aad"
profile_id: null
action: "share"
blocking: false
importance: "low"
intent_quote: "上限を定数にした理由を知っておきたい"
premise_quote: null
rationale_ref: null
assessed_by: "example-reviewer"
assessed_at: "2026-11-20T07:43:33Z"
---
```

### draft

```
---
type: "draft"
schema: 1
id: "20261120T074352Z-4371b4"
assessment_id: "20261120T074333Z-fd30af"
withdrawn_at: null
---
```

### revision（承認済み）

```
---
type: "revision"
schema: 1
draft_id: "20261120T074352Z-4371b4"
rev: 2
references: [{"kind": "repo", "url": "https://github.com/example-org/example-repo/blob/ec9b11f4752eadca7e100d863315c9f689286458/src/cart/total.ts#L5-L6"}]
changed_by: "agent:rehearsal"
changed_at: "2026-11-20T07:44:12Z"
reason_quote: "該当の行番号も書き添えてほしい"
approved_by: "example-reviewer"
approved_at: "2026-11-20T07:44:12Z"
---
question (non-blocking): 税額を含めた合計の端数処理について
（以下、下書きの本文。`rules.md` の 3 部形式）
```

### posting

```
---
type: "posting"
schema: 1
id: "20261120T074417Z-a34176"
draft_id: "20261120T074352Z-4371b4"
rev: 2
mode: "new"
github_comment_id: "123456789"
url: "https://github.com/example-org/example-repo/pull/12#discussion_r123456789"
payload_hash: "427cbd37f96dff09b275e1d71f16160c224950fd0eae91ee664cd412e81183ad"
anchor_verified: true
head_sha_at_post: "ec9b11f4752eadca7e100d863315c9f689286458"
posted_at: "2026-11-20T07:44:17Z"
outcome: "pending"
reply_refs: []
outcome_judged_by: null
---
```
