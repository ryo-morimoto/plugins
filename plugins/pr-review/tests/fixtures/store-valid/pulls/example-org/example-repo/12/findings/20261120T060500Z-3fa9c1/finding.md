---
type: "finding"
schema: 1
id: "20261120T060500Z-3fa9c1"
pull_id: "example-org/example-repo#12"
snapshot_id: "example-org/example-repo#12@a1b2c3d"
run_id: null
origin: "human"
origin_ref: "900000001"
title: "絞り込み条件が空のときの挙動が分かれていない"
body_hash: "1c6b8ec06106a426aad7f041cbac26eb3883194c76a3b203d840d48f6b12f796"
location: {"path": "src/orders/filter.ts", "start_line": 10, "end_line": 18, "side": "right"}
confidence: "unknown"
theme_key: null
norm_gap: null
norm_ref: null
dismissed_reason: null
created_by: "example-reviewer"
created_at: "2026-11-20T06:05:00Z"
---
絞り込み条件が空のとき、全件を返す経路と 0 件を返す経路が分かれていません。

どちらを期待しているのかを、呼び出し側から読み取れる形にしてほしいです。
