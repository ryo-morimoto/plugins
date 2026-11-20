import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN_ROOT / "skills" / "draft-review-comments" / "scripts" / "render-review-html.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_review_html", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SAMPLE = """## 下書き 1（気づき a。L10）

question (non-blocking): 最初の文です。次の文です。

- 項目の一つです。
  - 入れ子の項目です。
- 項目の二つめです。

<details>
<summary>確認したこと</summary>

- 詳しい事実です。

</details>

## 下書き 2（気づき b。L20）

二つめの下書きです。
"""


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def render(self, source, name="drafts.md"):
        return self.module.render_page(source, name, "タイトル")

    def test_one_section_per_heading(self):
        page = self.render(SAMPLE)
        self.assertEqual(page.count('<section class="draft"'), 2)
        self.assertIn('data-title="下書き 1（気づき a。L10）"', page)
        self.assertIn('data-title="下書き 2（気づき b。L20）"', page)

    def test_without_headings_the_whole_text_is_one_draft_named_after_the_file(self):
        page = self.render("本文だけです。\n", "rev-001.md")
        self.assertEqual(page.count('<section class="draft"'), 1)
        self.assertIn('data-title="rev-001.md"', page)

    def test_front_matter_is_skipped_and_line_numbers_stay_those_of_the_file(self):
        source = '---\ntype: "revision"\nrev: 1\n---\n本文の一文です。\n'
        page = self.render(source, "rev-001.md")
        self.assertNotIn("revision", page.split('<main id="drafts">')[1].split("</main>")[0])
        self.assertIn('data-line="5" data-raw="本文の一文です。"', page)

    def test_sentences_are_separate_commentable_units_with_source_lines(self):
        page = self.render(SAMPLE)
        self.assertIn('data-line="3" data-raw="question (non-blocking): 最初の文です。"', page)
        self.assertIn('data-line="3" data-raw="次の文です。"', page)
        self.assertIn('data-line="5" data-raw="項目の一つです。"', page)
        self.assertIn('data-line="6" data-raw="入れ子の項目です。"', page)

    def test_lists_nest_and_details_are_open(self):
        page = self.render(SAMPLE)
        outer = re.search(r"<ul><li>\s*(<span[^>]*>項目の一つです。</span>)\s*<ul><li>\s*<span[^>]*>入れ子の項目です。</span>\s*</li></ul>\s*</li><li>\s*<span[^>]*>項目の二つめです。</span>\s*</li></ul>", page)
        self.assertIsNotNone(outer)
        self.assertIn("<details open>", page)
        self.assertIn("<summary>", page)

    def test_sentences_are_not_split_inside_code_or_links(self):
        sentences = self.module.split_sentences("`a。b` と [c。d](https://example.com/x) です。次です。")
        self.assertEqual(sentences, ["`a。b` と [c。d](https://example.com/x) です。", "次です。"])

    def test_closing_brackets_stay_with_the_sentence(self):
        self.assertEqual(self.module.split_sentences("（これは補足です。）次です。"), ["（これは補足です。）", "次です。"])

    def test_html_in_the_source_is_escaped(self):
        page = self.render("## 下書き 1\n\n<script>alert(1)</script> と <img src=x onerror=alert(1)> です。\n")
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_only_http_links_become_anchors(self):
        page = self.render("## 下書き 1\n\n[安全](https://example.com/a) と [危険](javascript:alert(1)) です。\n")
        self.assertIn('<a href="https://example.com/a" target="_blank" rel="noopener noreferrer">安全</a>', page)
        self.assertNotIn('href="javascript:', page)

    def test_inline_code_and_bold(self):
        page = self.render("## 下書き 1\n\n**決めたいこと**: `meta` を直す。\n")
        self.assertIn("<strong>決めたいこと</strong>", page)
        self.assertIn("<code>meta</code>", page)

    def test_page_loads_nothing_from_outside(self):
        page = self.render(SAMPLE)
        self.assertIsNone(re.search(r"<script[^>]+src=", page))
        self.assertIsNone(re.search(r"<link\b", page))
        self.assertIsNone(re.search(r"(?:src|action)=[\"']https?:", page))
        self.assertNotIn("@import", page)

    def test_file_name_cannot_break_out_of_the_page(self):
        page = self.render(SAMPLE, 'a</script><script>alert(1)</script>.md')
        self.assertNotIn("<script>alert(1)</script>", page)

    @unittest.skipUnless(shutil.which("node"), "node が無いため、JavaScript の構文は確かめない")
    def test_embedded_script_is_valid_javascript(self):
        page = self.render(SAMPLE)
        script = page.split('<script>', 1)[1].split("</script>", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.js"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_same_input_gives_the_same_page(self):
        self.assertEqual(self.render(SAMPLE), self.render(SAMPLE))
        self.assertNotEqual(self.render(SAMPLE), self.render(SAMPLE + "追記です。\n"))


class CliTest(unittest.TestCase):
    def test_writes_the_page_and_creates_the_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "drafts.md"
            source.write_text(SAMPLE, encoding="utf-8")
            out = Path(directory) / "nested" / "review.html"
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("<!doctype html>"))

    def test_missing_input_exits_2_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "review.html"
            result = subprocess.run([sys.executable, str(SCRIPT), str(Path(directory) / "none.md"), "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("エラー", result.stderr)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
