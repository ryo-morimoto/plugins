#!/usr/bin/env bash
# 地図の画面を veriss で検査する。使い方と前提は README.md。
# 環境変数: VERISS（veriss の packages/veriss/src）、CHROME（ヘッドレスの Chromium）
set -u
here=$(cd "$(dirname "$0")" && pwd); map="$here/fixture/maps/all-states"; work=$(mktemp -d)
python3 "$here/../../skills/mapping-thought-experiments/scripts/thought_map.py" --root "$here/fixture" render "$map" >/dev/null || exit 2
fail=0
for state in "" "#4" "#5"; do  # 開いた直後（候補 1）、軸の候補を選んだ状態、前提のセルが光る状態
  "$CHROME" --headless --no-sandbox --disable-gpu --virtual-time-budget=3000 --dump-dom "file://$map/map.html$state" 2>/dev/null > "$work/dom.html"
  for part in header axes grid cands; do
    for range in "320 599" "600 999" "1000 1299" "1300 1600"; do  # 画面の切り替わり（600px、1000px）で分ける
      out=$(VERISS="$VERISS" node "$here/veriss_map.mjs" "$work/dom.html" $part $range) || { echo "ERROR ${state:-#1} $part $range"; fail=1; continue; }
      # 許す判定不能: 押せる範囲の大きさ（24px、WCAG 2.5.8）だけ。縦方向の大きさは検査の範囲外のため
      bad=$(python3 -c "import json,sys; r=json.loads(sys.argv[1]); print('' if set(r['byCode']) <= {'U_A11Y_TARGET_SIZE'} else r['sample'] or r['byCode'])" "$out")
      if [ -n "$bad" ]; then echo "NG ${state:-#1} $part $range: $bad"; fail=1; else echo "ok ${state:-#1} $part $range: $(python3 -c "import json,sys; r=json.loads(sys.argv[1]); print(r['status'], r['byCode'] or '')" "$out")"; fi
    done
  done
done
rm -rf "$work"; exit $fail
