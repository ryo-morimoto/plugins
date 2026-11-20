"""inventory.py のテスト。実行: python3 -m unittest discover -s plugins/naming/tests"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills/tellman-naming/scripts/inventory.py"

PY = '''
STATUS = {"open": 1}

def status(m):
    return m["status"]

PAGE = """<html><style>
.chip.used { color: red; }
.chip.flag { color: blue; }
:root { --line: #ccc; }
</style>
<div id="count" class="chip used"></div>
<script>
const counts = {};
function select(i, key) { return key; }
</script></html>"""
'''


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "app.py").write_text(PY, encoding="utf-8")
        (self.root / "conf.toml").write_text('[rows]\nchecked = true\n', encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        out = subprocess.run([sys.executable, str(SCRIPT), str(self.root), *args],
                             capture_output=True, text=True, check=True)
        return out.stdout

    def kinds(self):
        return {tuple(line.split("\t")[:2]) for line in self.run_script().splitlines()}

    def test_every_surface(self):
        kinds = self.kinds()
        for expected in [("py-constant", "STATUS"), ("py-function", "status"), ("data-key", "status"),
                         ("css-class", "flag"), ("css-var", "--line"), ("html-id", "count"),
                         ("js-binding", "counts"), ("js-function-or-class", "select"),
                         ("js-param", "key"), ("config-key", "checked")]:
            self.assertIn(expected, kinds)

    def test_collisions_find_one_word_with_two_kinds(self):
        out = self.run_script("--collisions")
        self.assertIn("status\t", out)  # 関数とデータのキー

    def test_unused_finds_dead_css_class(self):
        out = self.run_script("--unused")
        self.assertIn("css-class\tflag", out)
        self.assertNotIn("css-class\tused", out)

    def test_collisions_and_unused_together(self):
        out = self.run_script("--collisions", "--unused")
        self.assertIn("# collisions", out)
        self.assertIn("# unused", out)
        self.assertIn("css-class\tflag", out)

    def test_words_finds_leftovers(self):
        out = self.run_script("--words", "checked")
        self.assertIn("conf.toml:2:", out)


if __name__ == "__main__":
    unittest.main()
