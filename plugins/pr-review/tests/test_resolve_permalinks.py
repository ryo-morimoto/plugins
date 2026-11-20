import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "draft-review-comments" / "scripts" / "resolve-permalinks.py"
OWNER = "example-org"
REPO = "sample-repo"
MISSING_SHA = "0123456789abcdef0123456789abcdef01234567"


def git(directory, *args):
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "tester",
        "GIT_AUTHOR_EMAIL": "tester@example.invalid",
        "GIT_COMMITTER_NAME": "tester",
        "GIT_COMMITTER_EMAIL": "tester@example.invalid",
    }
    result = subprocess.run(["git", "-C", str(directory), *args], capture_output=True, text=True, env=env, check=True)
    return result.stdout.strip()


def write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def link(sha, path, fragment=""):
    return f"https://github.com/{OWNER}/{REPO}/blob/{sha}/{path}{fragment}"


class ResolvePermalinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.repo = Path(cls.tmp.name) / "repo"
        cls.repo.mkdir()
        git(cls.repo, "init", "-q")
        write_lines(cls.repo / "src" / "a.txt", ["one", "two", "three", "four", "five"])
        git(cls.repo, "add", "-A")
        git(cls.repo, "commit", "-q", "-m", "first")
        cls.first = git(cls.repo, "rev-parse", "HEAD")
        write_lines(cls.repo / "src" / "a.txt", [f"alpha{i}" for i in range(1, 9)])
        write_lines(cls.repo / "docs" / "b.md", ["# title", "body", "end"])
        git(cls.repo, "add", "-A")
        git(cls.repo, "commit", "-q", "-m", "second")
        cls.second = git(cls.repo, "rev-parse", "HEAD")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_cli(self, *args, stdin="", repo=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(repo or self.repo), *args],
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def resolve_one(self, text, *args):
        result = self.run_cli("--format", "json", *args, stdin=text)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(len(data["links"]), 1, data)
        return data["links"][0]

    def test_single_line(self):
        item = self.resolve_one(link(self.first, "src/a.txt", "#L3"))
        self.assertEqual(item["status"], "ok")
        self.assertEqual(item["lines"], ["three"])
        self.assertEqual((item["start"], item["end"]), (3, 3))
        self.assertEqual(item["file_lines"], 5)
        self.assertFalse(item["truncated"])

    def test_range(self):
        item = self.resolve_one(link(self.second, "src/a.txt", "#L2-L4"))
        self.assertEqual(item["status"], "ok")
        self.assertEqual(item["lines"], ["alpha2", "alpha3", "alpha4"])
        self.assertEqual((item["start"], item["end"]), (2, 4))

    def test_range_with_columns(self):
        item = self.resolve_one(link(self.second, "src/a.txt", "#L2C1-L3C5"))
        self.assertEqual(item["status"], "ok")
        self.assertEqual(item["lines"], ["alpha2", "alpha3"])

    def test_each_commit_gives_its_own_content(self):
        self.assertEqual(self.resolve_one(link(self.first, "src/a.txt", "#L1"))["lines"], ["one"])
        self.assertEqual(self.resolve_one(link(self.second, "src/a.txt", "#L1"))["lines"], ["alpha1"])
        self.assertEqual(self.resolve_one(link(self.first, "src/a.txt", "#L1"))["file_lines"], 5)

    def test_without_range_gives_file_lines_only(self):
        item = self.resolve_one(link(self.second, "docs/b.md"))
        self.assertEqual(item["status"], "ok")
        self.assertEqual(item["lines"], [])
        self.assertEqual(item["file_lines"], 3)
        self.assertIsNone(item["start"])
        self.assertIsNone(item["end"])

    def test_range_beyond_file(self):
        item = self.resolve_one(link(self.first, "src/a.txt", "#L4-L6"))
        self.assertEqual(item["status"], "range_out_of_bounds")
        self.assertEqual(item["lines"], [])
        self.assertEqual(item["file_lines"], 5)
        self.assertEqual(self.resolve_one(link(self.first, "src/a.txt", "#L6"))["status"], "range_out_of_bounds")

    def test_range_reversed(self):
        self.assertEqual(self.resolve_one(link(self.first, "src/a.txt", "#L4-L2"))["status"], "range_out_of_bounds")

    def test_line_zero(self):
        self.assertEqual(self.resolve_one(link(self.first, "src/a.txt", "#L0"))["status"], "range_out_of_bounds")

    def test_unreadable_fragment_is_out_of_bounds(self):
        self.assertEqual(self.resolve_one(link(self.first, "src/a.txt", "#L2-4"))["status"], "range_out_of_bounds")

    def test_commit_missing(self):
        item = self.resolve_one(link(MISSING_SHA, "src/a.txt", "#L1"))
        self.assertEqual(item["status"], "commit_missing")

    def test_not_pinned_branch_and_short_sha(self):
        self.assertEqual(self.resolve_one(link("main", "src/a.txt", "#L1"))["status"], "not_pinned")
        self.assertEqual(self.resolve_one(link(self.first[:7], "src/a.txt", "#L1"))["status"], "not_pinned")

    def test_path_missing(self):
        self.assertEqual(self.resolve_one(link(self.first, "src/none.txt", "#L1"))["status"], "path_missing")
        self.assertEqual(self.resolve_one(link(self.first, "docs/b.md", "#L1"))["status"], "path_missing")
        self.assertEqual(self.resolve_one(link(self.second, "src"))["status"], "path_missing")

    def test_repo_mismatch(self):
        text = link(self.first, "src/a.txt", "#L1")
        item = self.resolve_one(text, "--expect", "other-org/other-repo")
        self.assertEqual(item["status"], "repo_mismatch")
        self.assertEqual(self.resolve_one(text, "--expect", f"{OWNER}/{REPO}")["status"], "ok")

    def test_repo_mismatch_wins_over_not_pinned(self):
        item = self.resolve_one(link("main", "src/a.txt"), "--expect", "other-org/other-repo")
        self.assertEqual(item["status"], "repo_mismatch")

    def test_angle_brackets(self):
        item = self.resolve_one(f"see <{link(self.first, 'src/a.txt', '#L2')}> here")
        self.assertEqual(item["url"], link(self.first, "src/a.txt", "#L2"))
        self.assertEqual(item["lines"], ["two"])

    def test_markdown_link(self):
        url = link(self.first, "src/a.txt", "#L2-L3")
        item = self.resolve_one(f"[該当箇所]({url}) を参照")
        self.assertEqual(item["url"], url)
        self.assertEqual(item["lines"], ["two", "three"])

    def test_trailing_punctuation(self):
        url = link(self.first, "src/a.txt", "#L2")
        for suffix in [".", ",", ")", ").", ">.", ";", "!"]:
            with self.subTest(suffix=suffix):
                item = self.resolve_one(f"({url}{suffix}")
                self.assertEqual(item["url"], url)
                self.assertEqual(item["status"], "ok")

    def test_url_ends_at_fullwidth_punctuation_and_japanese_text(self):
        url = link(self.first, "src/a.txt", "#L2")
        for text in [f"（{url}）、次の文", f"[L2]({url})）、`x`", f"{url}。続き", f"「{url}」", f"{url}の行"]:
            with self.subTest(text=text):
                item = self.resolve_one(text)
                self.assertEqual(item["url"], url)
                self.assertEqual(item["status"], "ok")
                self.assertEqual(item["lines"], ["two"])

    def test_trailing_punctuation_without_fragment(self):
        url = link(self.second, "docs/b.md")
        self.assertEqual(self.resolve_one(f"{url}.")["url"], url)

    def test_duplicates_counted_once(self):
        url = link(self.first, "src/a.txt", "#L2")
        text = f"{url}\n[x]({url})\n<{url}>\n{url}."
        data = json.loads(self.run_cli("--format", "json", stdin=text).stdout)
        self.assertEqual(data["summary"], {"total": 1, "ok": 1, "problems": 0})

    def test_different_fragments_are_different_links(self):
        text = f"{link(self.first, 'src/a.txt', '#L1')} {link(self.first, 'src/a.txt', '#L2')}"
        data = json.loads(self.run_cli("--format", "json", stdin=text).stdout)
        self.assertEqual(data["summary"]["total"], 2)

    def test_non_github_and_non_blob_urls_ignored(self):
        text = "\n".join(
            [
                "https://example.com/a/b/blob/" + self.first + "/src/a.txt#L1",
                "https://gitlab.com/a/b/-/blob/" + self.first + "/src/a.txt#L1",
                f"https://github.com/{OWNER}/{REPO}/pull/12",
                f"https://github.com/{OWNER}/{REPO}/issues/3",
                f"https://github.com/{OWNER}/{REPO}/commit/{self.first}",
                f"https://github.com/{OWNER}/{REPO}/tree/{self.first}/src",
                f"https://github.com/{OWNER}/{REPO}/blob/{self.first}",
            ]
        )
        result = self.run_cli("--format", "json", stdin=text)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["links"], [])
        self.assertEqual(data["summary"], {"total": 0, "ok": 0, "problems": 0})

    def test_ignored_urls_do_not_hide_real_ones(self):
        text = f"https://github.com/{OWNER}/{REPO}/pull/12 と {link(self.first, 'src/a.txt', '#L1')}"
        data = json.loads(self.run_cli("--format", "json", stdin=text).stdout)
        self.assertEqual(data["summary"]["total"], 1)

    def test_truncated(self):
        item = self.resolve_one(link(self.second, "src/a.txt", "#L1-L8"), "--max-lines", "3")
        self.assertEqual(item["status"], "ok")
        self.assertTrue(item["truncated"])
        self.assertEqual(item["lines"], ["alpha1", "alpha2", "alpha3"])

    def test_not_truncated_at_the_limit(self):
        item = self.resolve_one(link(self.second, "src/a.txt", "#L1-L3"), "--max-lines", "3")
        self.assertFalse(item["truncated"])
        self.assertEqual(len(item["lines"]), 3)

    def test_default_max_lines_is_eight(self):
        write_lines(self.repo / "long.txt", [f"row{i}" for i in range(1, 13)])
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "long")
        sha = git(self.repo, "rev-parse", "HEAD")
        item = self.resolve_one(link(sha, "long.txt", "#L1-L12"))
        self.assertTrue(item["truncated"])
        self.assertEqual(len(item["lines"]), 8)

    def test_exit_code_all_ok(self):
        result = self.run_cli(stdin=link(self.first, "src/a.txt", "#L1"))
        self.assertEqual(result.returncode, 0)

    def test_exit_code_with_problems(self):
        text = f"{link(self.first, 'src/a.txt', '#L1')} {link('main', 'src/a.txt', '#L1')}"
        result = self.run_cli("--format", "json", stdin=text)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["summary"], {"total": 2, "ok": 1, "problems": 1})

    def test_exit_code_not_a_git_repository(self):
        with tempfile.TemporaryDirectory() as plain:
            result = self.run_cli(stdin=link(self.first, "src/a.txt"), repo=plain)
        self.assertEqual(result.returncode, 2)
        self.assertIn("git リポジトリではありません", result.stderr)

    def test_exit_code_bad_usage(self):
        self.assertEqual(self.run_cli("--max-lines", "0").returncode, 2)
        self.assertEqual(self.run_cli("--expect", "no-slash").returncode, 2)
        self.assertEqual(self.run_cli("--format", "xml").returncode, 2)

    def test_exit_code_missing_input_file(self):
        result = self.run_cli(str(Path(self.tmp.name) / "none.md"))
        self.assertEqual(result.returncode, 2)

    def test_no_links(self):
        result = self.run_cli(stdin="リンクのない文章です。\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("固定リンクは見つかりませんでした", result.stdout)
        data = json.loads(self.run_cli("--format", "json", stdin="").stdout)
        self.assertEqual(data["summary"], {"total": 0, "ok": 0, "problems": 0})

    def test_json_shape(self):
        text = f"{link(self.first, 'src/a.txt', '#L2-L3')}\n{link('main', 'src/a.txt')}"
        result = self.run_cli("--format", "json", stdin=text)
        data = json.loads(result.stdout)
        self.assertEqual(set(data), {"note", "links", "summary"})
        self.assertIn("関連性は確認していません", data["note"])
        keys = {"url", "owner", "repo", "ref", "path", "start", "end", "status", "file_lines", "lines", "truncated"}
        for item in data["links"]:
            self.assertEqual(set(item), keys)
        first = data["links"][0]
        self.assertEqual(first["owner"], OWNER)
        self.assertEqual(first["repo"], REPO)
        self.assertEqual(first["ref"], self.first)
        self.assertEqual(first["path"], "src/a.txt")
        self.assertEqual(data["links"][1]["status"], "not_pinned")

    def test_text_format(self):
        result = self.run_cli(stdin=f"{link(self.first, 'src/a.txt', '#L2-L3')}\n{link('main', 'src/a.txt')}")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.startswith("関連性は確認していません。行の存在と本文だけを示します"))
        self.assertIn("[ok]", result.stdout)
        self.assertIn("two", result.stdout)
        self.assertIn("[not_pinned]", result.stdout)

    def test_text_is_default_format(self):
        result = self.run_cli(stdin=link(self.first, "src/a.txt", "#L1"))
        self.assertIn("[ok]", result.stdout)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(result.stdout)

    def test_reads_stdin_with_dash(self):
        result = self.run_cli("--format", "json", "-", stdin=link(self.first, "src/a.txt", "#L1"))
        self.assertEqual(json.loads(result.stdout)["links"][0]["lines"], ["one"])

    def test_reads_stdin_without_arguments(self):
        result = self.run_cli("--format", "json", stdin=link(self.first, "src/a.txt", "#L5"))
        self.assertEqual(json.loads(result.stdout)["links"][0]["lines"], ["five"])

    def test_reads_files_and_merges_them(self):
        a = Path(self.tmp.name) / "a.md"
        b = Path(self.tmp.name) / "b.md"
        a.write_text(link(self.first, "src/a.txt", "#L1"), encoding="utf-8")
        b.write_text(link(self.first, "src/a.txt", "#L1") + "\n" + link(self.first, "src/a.txt", "#L2"), encoding="utf-8")
        result = self.run_cli("--format", "json", str(a), str(b))
        self.assertEqual(json.loads(result.stdout)["summary"]["total"], 2)

    def test_crlf_lines_have_no_carriage_return(self):
        (self.repo / "crlf.txt").write_bytes(b"first\r\nsecond\r\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "crlf")
        sha = git(self.repo, "rev-parse", "HEAD")
        item = self.resolve_one(link(sha, "crlf.txt", "#L1-L2"))
        self.assertEqual(item["lines"], ["first", "second"])
        self.assertEqual(item["file_lines"], 2)


if __name__ == "__main__":
    unittest.main()
