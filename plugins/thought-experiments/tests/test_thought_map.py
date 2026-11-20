"""thought_map.py のテスト。実行: python3 -m unittest discover -s plugins/thought-experiments/tests"""

from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills/mapping-thought-experiments/scripts"
sys.path.insert(0, str(SCRIPTS))

import thought_map  # noqa: E402

MAP = """
title = "例"
question = "問い"

[rows]
name = "行"
basis = "own"
ref = "notes.md"
ref_read = true

[[rows.values]]
id = "a"
name = "A"

[[rows.values]]
id = "b"
name = "B"

[cols]
name = "列"
basis = "standard"
ref = "https://example.org/std"
ref_read = true

[[cols.values]]
id = "x"
name = "X"

[[cols.values]]
id = "y"
name = "Y"

[[cells]]
row = "a"
col = "x"
status = "supported"
claim = "ax の結論 </script><img src=x onerror=alert(1)>"
evidence = ["notes.md"]

[[cells]]
row = "b"
col = "y"
status = "refuted"
claim = "by の結論"
evidence = ["notes.md"]
"""


class ThoughtMapTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "notes.md").write_text("x", encoding="utf-8")
        self.dir = self.root / "maps/demo"
        self.dir.mkdir(parents=True)
        (self.dir / "map.toml").write_text(MAP, encoding="utf-8")
        thought_map.ROOT = self.root

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = thought_map.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def test_valid_map(self):
        self.assertEqual(thought_map.validate(thought_map.load(self.dir)), [])

    def test_invalid_cell(self):
        (self.dir / "map.toml").write_text(MAP + '\n[[cells]]\nrow = "a"\ncol = "z"\nstatus = "maybe"\n',
                                           encoding="utf-8")
        errs = thought_map.validate(thought_map.load(self.dir))
        self.assertTrue(any("軸の値にない" in e for e in errs))
        self.assertTrue(any("status は" in e for e in errs))

    def test_missing_evidence(self):
        (self.root / "notes.md").unlink()
        errs = thought_map.validate(thought_map.load(self.dir))
        self.assertTrue(any("根拠 notes.md" in e for e in errs))

    def test_candidates_use_both_neighbours(self):
        by_target = {cand.target: cand for cand in thought_map.candidates(thought_map.load(self.dir))}
        # a/y は、同じ行の a/x と同じ列の b/y の両方を前提にする
        self.assertEqual(by_target["a/y"].mode, "constructive")
        self.assertEqual(sorted(by_target["a/y"].premises), ["a/x", "b/y"])
        # 自作の行の軸は「根拠を探す」候補になり、空のセルより上に来る
        order = [cand.target for cand in thought_map.candidates(thought_map.load(self.dir))]
        self.assertLess(order.index("axis:rows"), order.index("b/x"))
        self.assertNotIn("axis:cols", order)

    def test_render_then_check(self):
        self.assertEqual(self.run_cli("check")[0], 1)  # map.html がまだない
        self.assertEqual(self.run_cli("render")[0], 0)
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0, out)
        (self.dir / "map.toml").write_text(MAP.replace("問い", "変えた問い"), encoding="utf-8")
        self.assertEqual(self.run_cli("check")[0], 1)  # 古い map.html を検出する

    def test_html_does_not_break_out_of_script(self):
        self.run_cli("render")
        page = (self.dir / "map.html").read_text(encoding="utf-8")
        data = re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S).group(1)
        self.assertNotIn("</script", data)
        self.assertIn('"up": "../../"', data)
        self.assertIn('"map_dir": "maps/demo"', data)


if __name__ == "__main__":
    unittest.main()
