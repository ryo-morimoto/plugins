import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN_ROOT / "skills" / "draft-review-comments" / "scripts" / "import-findings.py"
FIXTURE = PLUGIN_ROOT / "tests" / "fixtures" / "pr-tour-export.json"
PULL_DIR = Path("pulls") / "example-org" / "example-repo" / "12"
ID_PATTERN = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{6}")

PULL_KEYS = {"type", "schema", "id", "url", "series", "title", "author", "fetched_at"}
SNAPSHOT_KEYS = {"type", "schema", "id", "pull_id", "head_sha", "base_sha", "fetched_at"}
FINDING_KEYS = {
    "type", "schema", "id", "pull_id", "snapshot_id", "run_id", "origin", "origin_ref", "title",
    "body_hash", "location", "confidence", "theme_key", "norm_gap", "norm_ref", "dismissed_reason",
    "created_by", "created_at",
}


def load_module():
    spec = importlib.util.spec_from_file_location("import_findings", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GIT = ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false"]


def make_repo(directory, export):
    """書き出しの各コメントが指す行を持つファイルだけの、一時的なリポジトリを作る。"""
    directory.mkdir()
    for comment in export["comments"]:
        target = directory / comment["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        filler = [f"// line {number}" for number in range(1, comment["startLine"])]
        target.write_text("\n".join(filler + comment["code"].split("\n") + ["// end"]) + "\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(directory)], check=True)
    subprocess.run([*GIT, "-C", str(directory), "add", "."], check=True)
    subprocess.run([*GIT, "-C", str(directory), "commit", "-q", "-m", "fixture"], check=True)
    result = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def read_record(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "---"
    end = lines.index("---", 1)
    meta = {}
    for line in lines[1:end]:
        key, separator, raw = line.partition(": ")
        assert separator, line
        meta[key] = json.loads(raw)
    return meta, "\n".join(lines[end + 1 :]).strip("\n")


class ImportFindingsTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.store = self.tmp / "store"
        self.export = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.repo = self.tmp / "repo"
        self.commit = make_repo(self.repo, self.export)
        for comment in self.export["comments"]:
            comment["commit"] = self.commit

    def write_export(self, data, name="export.json"):
        path = self.tmp / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def run_import(self, *extra, source=None):
        source = source or self.write_export(self.export, "default.json")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--store", str(self.store), "--repo", str(self.repo), "--from", str(source), *extra],
            capture_output=True,
            text=True,
        )

    def findings(self):
        found = {}
        for record in sorted((self.store / PULL_DIR / "findings").glob("*/finding.md")):
            meta, body = read_record(record)
            self.assertEqual(record.parent.name, meta["id"])
            found[meta["origin_ref"]] = (meta, body, record)
        return found

    def snapshot_files(self):
        return sorted(path for path in self.store.rglob("*") if path.is_file())

    def test_creates_records_in_layout(self):
        result = self.run_import("--series", "EX-1")
        self.assertEqual(result.returncode, 0, result.stderr)

        pull, pull_body = read_record(self.store / PULL_DIR / "pull.md")
        self.assertEqual(set(pull), PULL_KEYS)
        self.assertEqual(pull["type"], "pull")
        self.assertEqual(pull["schema"], 1)
        self.assertEqual(pull["id"], "example-org/example-repo#12")
        self.assertEqual(pull["url"], "https://github.com/example-org/example-repo/pull/12")
        self.assertIsNone(pull["title"])
        self.assertIsNone(pull["author"])
        self.assertRegex(pull["fetched_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(pull_body, "")

        snapshot, _ = read_record(self.store / PULL_DIR / "snapshots" / "1111111.md")
        self.assertEqual(set(snapshot), SNAPSHOT_KEYS)
        self.assertEqual(snapshot["type"], "snapshot")
        self.assertEqual(snapshot["id"], "example-org/example-repo#12@1111111")
        self.assertEqual(snapshot["pull_id"], pull["id"])
        self.assertEqual(snapshot["head_sha"], self.export["head"])
        self.assertEqual(snapshot["base_sha"], self.export["base"])

        found = self.findings()
        self.assertEqual(set(found), {"c-001", "c-002", "c-003"})
        for origin_ref, (meta, _, _) in found.items():
            self.assertEqual(set(meta), FINDING_KEYS)
            self.assertEqual(meta["type"], "finding")
            self.assertEqual(meta["schema"], 1)
            self.assertRegex(meta["id"], ID_PATTERN)
            self.assertEqual(meta["pull_id"], pull["id"])
            self.assertEqual(meta["snapshot_id"], snapshot["id"])
            self.assertEqual(meta["origin"], "human")
            self.assertEqual(meta["confidence"], "unknown")
            for key in ("run_id", "theme_key", "norm_gap", "norm_ref", "dismissed_reason"):
                self.assertIsNone(meta[key], key)

    def test_front_matter_is_one_json_value_per_line(self):
        self.run_import()
        for _, (_, _, record) in self.findings().items():
            lines = record.read_text(encoding="utf-8").split("\n")
            end = lines.index("---", 1)
            self.assertGreater(end, 1)
            for line in lines[1:end]:
                key, separator, raw = line.partition(": ")
                self.assertTrue(separator and key, line)
                json.loads(raw)

    def test_body_hash_and_title(self):
        self.run_import()
        found = self.findings()
        for comment in self.export["comments"]:
            meta, body, _ = found[comment["id"]]
            expected = comment["body"].strip("\r\n")
            self.assertEqual(body, expected)
            self.assertEqual(meta["body_hash"], hashlib.sha256(expected.encode("utf-8")).hexdigest())
            self.assertEqual(meta["created_at"], comment["createdAt"])
        self.assertEqual(found["c-001"][0]["title"], "税額の端数処理がここだけ丸めずに返っています。")
        self.assertEqual(found["c-002"][0]["title"], "割引率の上限を定数にした意図を知りたいです。")

    def test_multiline_body_keeps_line_breaks(self):
        self.run_import()
        _, body, _ = self.findings()["c-002"]
        self.assertEqual(
            body.split("\n"),
            [
                "割引率の上限を定数にした意図を知りたいです。",
                "",
                "- 将来、ユーザーごとに変える予定か",
                "- 変えるなら、設定として外に出す案もある",
            ],
        )

    def test_title_skips_blank_lines_and_is_cut_at_120(self):
        self.export["comments"] = [dict(self.export["comments"][0], body="\n \n  " + "あ" * 130 + "\n次の行")]
        source = self.write_export(self.export)
        self.assertEqual(self.run_import(source=source).returncode, 0)
        meta, body, _ = self.findings()["c-001"]
        self.assertEqual(meta["title"], "あ" * 120)
        self.assertEqual(body, " \n  " + "あ" * 130 + "\n次の行")

    def test_location(self):
        self.run_import()
        found = self.findings()
        self.assertEqual(
            found["c-001"][0]["location"],
            {"path": "src/cart/total.ts", "start_line": 10, "end_line": 12, "side": "right"},
        )
        self.assertEqual(
            found["c-003"][0]["location"],
            {"path": "src/cart/legacy-total.ts", "start_line": 21, "end_line": 23, "side": "left"},
        )
        self.assertEqual(list(found["c-003"][0]["location"]), ["path", "start_line", "end_line", "side"])

    def test_rerun_skips_existing_findings(self):
        self.run_import()
        before = {path: path.read_text(encoding="utf-8") for path in self.snapshot_files()}
        result = self.run_import()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("作成 0 件 / スキップ 3 件 / 衝突 0 件", result.stdout)
        self.assertEqual({path: path.read_text(encoding="utf-8") for path in self.snapshot_files()}, before)
        self.assertEqual(len(self.findings()), 3)

    def test_changed_body_is_reported_as_conflict_without_overwrite(self):
        self.run_import()
        before = {path: path.read_text(encoding="utf-8") for path in self.snapshot_files()}
        self.export["comments"][0]["body"] = "本文を書き換えました。"
        result = self.run_import(source=self.write_export(self.export))
        self.assertEqual(result.returncode, 1)
        self.assertIn("衝突", result.stdout)
        self.assertIn("作成 0 件 / スキップ 2 件 / 衝突 1 件", result.stdout)
        self.assertEqual({path: path.read_text(encoding="utf-8") for path in self.snapshot_files()}, before)

    def test_dry_run_writes_nothing(self):
        result = self.run_import("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("作成 3 件", result.stdout)
        self.assertFalse(self.store.exists())

    def test_series_and_created_by(self):
        self.run_import("--series", "EX-1", "--created-by", "agent:importer")
        pull, _ = read_record(self.store / PULL_DIR / "pull.md")
        self.assertEqual(pull["series"], "EX-1")
        for meta, _, _ in self.findings().values():
            self.assertEqual(meta["created_by"], "agent:importer")

    def test_defaults_for_series_and_created_by(self):
        self.run_import()
        pull, _ = read_record(self.store / PULL_DIR / "pull.md")
        self.assertIsNone(pull["series"])
        for meta, _, _ in self.findings().values():
            self.assertEqual(meta["created_by"], "unknown")

    def test_invalid_input_exits_2_and_writes_nothing(self):
        def without_comments(data):
            del data["comments"]

        def mutate(change):
            data = copy.deepcopy(self.export)
            change(data)
            return data

        cases = {
            "schemaVersion が 2": mutate(lambda d: d.update(schemaVersion=2)),
            "schemaVersion が文字列": mutate(lambda d: d.update(schemaVersion="1")),
            "kind が違う": mutate(lambda d: d.update(kind="other")),
            "prUrl が PR の URL でない": mutate(lambda d: d.update(prUrl="https://github.com/example-org/example-repo")),
            "prUrl が issue の URL": mutate(lambda d: d.update(prUrl="https://github.com/example-org/example-repo/issues/12")),
            "comments が無い": mutate(without_comments),
            "comments が配列でない": mutate(lambda d: d.update(comments={})),
            "side が不正": mutate(lambda d: d["comments"][0].update(side="both")),
            "行が逆順": mutate(lambda d: d["comments"][0].update(startLine=9, endLine=3)),
            "id が重複": mutate(lambda d: d["comments"][1].update(id="c-001")),
            "body が空": mutate(lambda d: d["comments"][0].update(body="\n\n")),
            "head が 40 桁でない": mutate(lambda d: d.update(head="abc")),
            "commit が無い": mutate(lambda d: d["comments"][0].pop("commit")),
            "commit が 40 桁でない": mutate(lambda d: d["comments"][0].update(commit="abc")),
            "code が無い": mutate(lambda d: d["comments"][0].pop("code")),
            "code が空": mutate(lambda d: d["comments"][0].update(code="")),
        }
        for name, data in cases.items():
            with self.subTest(name):
                result = self.run_import(source=self.write_export(data))
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("エラー", result.stderr)
                self.assertFalse(self.store.exists())

    def assert_rejected(self, data, *messages, extra=()):
        result = self.run_import(*extra, source=self.write_export(data))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        for message in messages:
            self.assertIn(message, result.stderr)
        self.assertFalse(self.store.exists())

    def test_code_that_differs_from_the_repository_is_rejected(self):
        self.export["comments"][1]["code"] = "export const MAX_DISCOUNT = 0.8;"
        self.assert_rejected(self.export, "c-002", "一致しません")

    def test_trailing_whitespace_difference_is_rejected(self):
        self.export["comments"][1]["code"] += " "
        self.assert_rejected(self.export, "c-002")

    def test_line_range_beyond_the_file_is_rejected(self):
        self.export["comments"][0].update(startLine=40, endLine=42)
        self.assert_rejected(self.export, "c-001", "にありません")

    def test_every_mismatch_is_reported_at_once(self):
        self.export["comments"][0]["code"] = "x"
        self.export["comments"][2]["code"] = "y"
        self.assert_rejected(self.export, "c-001", "c-003")

    def test_commit_missing_from_the_repository_is_rejected(self):
        self.export["comments"][0]["commit"] = "9" * 40
        self.assert_rejected(self.export, "c-001", "fetch")

    def test_path_missing_at_the_commit_is_rejected(self):
        self.export["comments"][0]["path"] = "src/cart/other.ts"
        self.assert_rejected(self.export, "c-001", "読めません")

    def test_dry_run_also_verifies(self):
        self.export["comments"][0]["code"] = "x"
        self.assert_rejected(self.export, "c-001", extra=("--dry-run",))

    def test_repo_is_required(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--store", str(self.store), "--from", str(FIXTURE)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--repo", result.stderr)

    def test_crlf_files_match_lf_code(self):
        target = self.repo / "src/cart/discount.ts"
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
        subprocess.run([*GIT, "-C", str(self.repo), "commit", "-q", "-a", "-m", "crlf"], check=True)
        head = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        self.export["comments"][1]["commit"] = head.stdout.strip()
        self.assertEqual(self.run_import(source=self.write_export(self.export)).returncode, 0)

    def test_real_export_shape_uuid_id_tab_and_japanese_code(self):
        comment = {
            "id": "c6df291d-4545-4978-9de8-db1c28173d47", "path": "src/amount.ts", "side": "right",
            "commit": "0" * 40, "startLine": 3, "endLine": 3,
            "code": "\t * 合計の端数は、ここで丸めない（日本語の注釈）", "body": "丸める場所を、確認したいです。",
            "createdAt": "2026-11-20T03:45:11.533Z", "updatedAt": "2026-11-20T03:45:11.533Z",
        }
        export = copy.deepcopy(self.export)
        export["comments"] = [comment]
        self.repo = self.tmp / "repo-real"
        comment["commit"] = make_repo(self.repo, export)
        result = self.run_import(source=self.write_export(export))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        meta, _, _ = self.findings()[comment["id"]]
        self.assertEqual(meta["origin_ref"], comment["id"])

    def test_unreadable_input_exits_2(self):
        broken = self.tmp / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        for name, source in {"JSON でない": broken, "ファイルが無い": self.tmp / "missing.json"}.items():
            with self.subTest(name):
                result = self.run_import(source=source)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.store.exists())

    def test_ids_do_not_collide_within_the_same_second(self):
        self.export["comments"] = [
            dict(self.export["comments"][0], id=f"c-{index:03d}", body=f"気づき {index}") for index in range(200)
        ]
        self.assertEqual(self.run_import(source=self.write_export(self.export)).returncode, 0)
        ids = [meta["id"] for meta, _, _ in self.findings().values()]
        self.assertEqual(len(ids), 200)
        self.assertEqual(len(set(ids)), 200)

    def test_id_generation_retries_on_collision(self):
        module = load_module()
        moment = datetime(2026, 11, 20, 6, 5, 0, tzinfo=timezone.utc)
        taken = set()
        with mock.patch.object(module.secrets, "token_hex", side_effect=["aaaaaa", "aaaaaa", "bbbbbb"]):
            first = module.new_finding_id(moment, taken)
            second = module.new_finding_id(moment, taken)
        self.assertEqual(first, "20261120T060500Z-aaaaaa")
        self.assertEqual(second, "20261120T060500Z-bbbbbb")

    def test_new_id_avoids_existing_finding_directory(self):
        module = load_module()
        moment = datetime(2026, 11, 20, 6, 5, 0, tzinfo=timezone.utc)
        taken = {"20261120T060500Z-aaaaaa"}
        with mock.patch.object(module.secrets, "token_hex", side_effect=["aaaaaa", "cccccc"]):
            self.assertEqual(module.new_finding_id(moment, taken), "20261120T060500Z-cccccc")


if __name__ == "__main__":
    unittest.main()
