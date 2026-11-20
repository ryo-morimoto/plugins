import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
SCRIPT = TESTS.parent / "skills" / "draft-review-comments" / "scripts" / "validate-records.py"
FIXTURE = TESTS / "fixtures" / "store-valid"

PR = "pulls/example-org/example-repo/12"
F1 = "20261120T060500Z-3fa9c1"
F2 = "20261120T060512Z-b7e204"
A1 = "20261120T061000Z-c04d19"
D1 = "20261120T062000Z-91b3e8"
P1 = "20261120T064500Z-e6120d"
FINDING1 = f"{PR}/findings/{F1}/finding.md"
FINDING2 = f"{PR}/findings/{F2}/finding.md"
ASSESSMENT1 = f"{PR}/findings/{F1}/assessments/{A1}.md"
DRAFT = f"{PR}/findings/{F1}/drafts/{D1}/draft.md"
REV1 = f"{PR}/findings/{F1}/drafts/{D1}/rev-001.md"
REV2 = f"{PR}/findings/{F1}/drafts/{D1}/rev-002.md"
POSTING = f"{PR}/findings/{F1}/drafts/{D1}/postings/{P1}.md"
SNAPSHOT = f"{PR}/snapshots/a1b2c3d.md"
PULL = f"{PR}/pull.md"


def run_validator(store, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--store", str(store), *extra],
        capture_output=True, text=True, encoding="utf-8",
    )


class StoreCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name) / "store"
        shutil.copytree(FIXTURE, self.store)

    def path(self, rel):
        return self.store / rel

    def read(self, rel):
        return self.path(rel).read_text(encoding="utf-8")

    def write(self, rel, text):
        self.path(rel).write_text(text, encoding="utf-8")

    def set_field(self, rel, key, value):
        lines = self.read(rel).split("\n")
        prefix = f"{key}: "
        index = next(i for i, line in enumerate(lines) if line.startswith(prefix))
        lines[index] = f"{prefix}{json.dumps(value, ensure_ascii=False)}"
        self.write(rel, "\n".join(lines))

    def remove_field(self, rel, key):
        lines = self.read(rel).split("\n")
        self.write(rel, "\n".join(line for line in lines if not line.startswith(f"{key}: ")))

    def errors(self):
        result = run_validator(self.store, "--format", "json")
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return json.loads(result.stdout)["errors"]

    def assertRule(self, rule, path=None):
        errors = self.errors()
        hits = [e for e in errors if e["rule"] == rule and (path is None or e["path"] == path)]
        self.assertTrue(hits, f"規則 {rule}（{path}）のエラーが出ていません。実際: {errors}")
        self.assertEqual(run_validator(self.store).returncode, 1)
        return hits


class FixtureTest(StoreCase):
    def test_valid_fixture_has_no_errors(self):
        result = run_validator(self.store)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("エラーなし", result.stdout)

    def test_json_output_is_readable(self):
        result = run_validator(self.store, "--format", "json")
        data = json.loads(result.stdout)
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["checked"], 10)

    def test_text_output_lists_path_rule_message_and_count(self):
        self.set_field(FINDING1, "confidence", "maybe")
        result = run_validator(self.store)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{FINDING1.removeprefix('pulls/')}: [1] confidence:", result.stdout)
        self.assertIn("エラー 1 件", result.stdout)

    def test_missing_pulls_directory_exits_2(self):
        empty = self.store.parent / "empty"
        empty.mkdir()
        result = run_validator(empty)
        self.assertEqual(result.returncode, 2)
        self.assertIn("pulls", result.stderr)


class RuleTest(StoreCase):
    def test_rule1_missing_required_field(self):
        self.remove_field(FINDING1, "title")
        self.assertRule(1)

    def test_rule1_invalid_enum(self):
        self.set_field(ASSESSMENT1, "action", "ignore")
        self.assertRule(1)

    def test_rule1_wrong_type(self):
        self.set_field(ASSESSMENT1, "blocking", "false")
        self.assertRule(1)

    def test_rule1_stage1_null_only_field(self):
        self.set_field(FINDING1, "run_id", "run-1")
        self.assertRule(1)

    def test_rule1_unreadable_json_line(self):
        self.write(FINDING1, self.read(FINDING1).replace('title: "', "title: 引用符なし ", 1))
        hits = self.assertRule(1)
        self.assertTrue(any("JSON" in e["message"] for e in hits))

    def test_rule1_missing_front_matter(self):
        self.write(PULL, "本文だけのファイル\n")
        self.assertRule(1)

    def test_rule2_unsupported_stage2_type(self):
        self.set_field(DRAFT, "type", "claim")
        hits = self.assertRule(2)
        self.assertIn("未対応", hits[0]["message"])

    def test_rule2_unknown_type(self):
        self.set_field(DRAFT, "type", "nonsense")
        self.assertRule(2)

    def test_rule3_finding_folder_differs_from_id(self):
        folder = self.path(f"{PR}/findings/{F1}")
        folder.rename(folder.with_name("20261120T060500Z-000000"))
        self.assertRule(3)

    def test_rule3_pull_folder_differs_from_pull_id(self):
        folder = self.path(PR)
        folder.rename(folder.with_name("13"))
        self.assertRule(3)

    def test_rule3_assessment_finding_id_differs_from_parent_folder(self):
        self.set_field(ASSESSMENT1, "finding_id", F2)
        self.assertRule(3, ASSESSMENT1.removeprefix("pulls/"))

    def test_rule3_snapshot_file_name_differs_from_head(self):
        self.path(SNAPSHOT).rename(self.path(f"{PR}/snapshots/ffffff0.md"))
        self.assertRule(3)

    def test_rule3_type_differs_from_location(self):
        self.set_field(REV2, "type", "posting")
        self.assertRule(3)

    def test_rule4_missing_snapshot(self):
        self.set_field(FINDING1, "snapshot_id", "example-org/example-repo#12@0000000")
        self.assertRule(4, FINDING1.removeprefix("pulls/"))

    def test_rule4_missing_pull(self):
        self.set_field(SNAPSHOT, "pull_id", "example-org/example-repo#99")
        self.assertRule(4, SNAPSHOT.removeprefix("pulls/"))

    def test_rule4_missing_assessment(self):
        self.set_field(DRAFT, "assessment_id", "20261120T000000Z-000000")
        self.assertRule(4, DRAFT.removeprefix("pulls/"))

    def test_rule4_missing_draft(self):
        self.set_field(POSTING, "draft_id", "20261120T000000Z-000000")
        self.assertRule(4, POSTING.removeprefix("pulls/"))

    def test_rule5_body_changed_after_hash(self):
        self.write(FINDING1, self.read(FINDING1) + "\n追記した一文です。\n")
        self.assertRule(5)

    def test_rule5_surrounding_newlines_are_ignored(self):
        self.write(FINDING1, self.read(FINDING1).replace("---\n絞り込み", "---\n\n絞り込み", 1).rstrip("\n") + "\n\n\n")
        self.assertEqual(self.errors(), [])

    def test_rule6_missing_revision_number(self):
        self.path(REV1).unlink()
        self.assertRule(6)

    def test_rule6_rev_differs_from_file_name(self):
        self.set_field(REV2, "rev", 3)
        self.assertRule(6, REV2.removeprefix("pulls/"))

    def test_rule7_only_approved_by_filled(self):
        self.set_field(REV2, "approved_by", "example-reviewer")
        self.assertRule(7, REV2.removeprefix("pulls/"))

    def test_rule7_only_approved_at_filled(self):
        self.set_field(REV1, "approved_by", None)
        self.assertRule(7, REV1.removeprefix("pulls/"))

    def test_rule8_posting_to_unapproved_revision(self):
        self.set_field(POSTING, "rev", 2)
        hits = self.assertRule(8)
        self.assertIn("承認されていません", hits[0]["message"])

    def test_rule8_posting_to_missing_revision(self):
        self.set_field(POSTING, "rev", 5)
        self.assertRule(8)

    def test_rule9_duplicate_posting_for_same_draft_rev_mode(self):
        copy_id = "20261120T065000Z-aaaaaa"
        text = self.read(POSTING).replace(f'id: "{P1}"', f'id: "{copy_id}"', 1)
        self.write(f"{PR}/findings/{F1}/drafts/{D1}/postings/{copy_id}.md", text)
        self.assertRule(9)

    def test_rule9_different_mode_is_allowed(self):
        copy_id = "20261120T065000Z-aaaaaa"
        text = self.read(POSTING).replace(f'id: "{P1}"', f'id: "{copy_id}"', 1).replace('mode: "new"', 'mode: "edit"')
        self.write(f"{PR}/findings/{F1}/drafts/{D1}/postings/{copy_id}.md", text)
        self.assertEqual(self.errors(), [])

    def test_rule10_start_line_after_end_line(self):
        self.set_field(FINDING1, "location", {"path": "src/a.ts", "start_line": 20, "end_line": 10, "side": "right"})
        self.assertRule(10)

    def test_rule10_start_line_below_one(self):
        self.set_field(FINDING1, "location", {"path": "src/a.ts", "start_line": 0, "end_line": 3, "side": "left"})
        self.assertRule(10)

    def test_rule11_repo_reference_not_pinned_to_sha(self):
        ref = {"kind": "repo", "url": "https://github.com/example-org/example-repo/blob/main/src/orders/filter.ts#L10-L18"}
        self.set_field(REV1, "references", [ref])
        self.assertRule(11, REV1.removeprefix("pulls/"))

    def test_rule11_repo_reference_with_short_sha(self):
        ref = {"kind": "repo", "url": "https://github.com/example-org/example-repo/blob/a1b2c3d/src/orders/filter.ts"}
        self.set_field(REV1, "references", [ref])
        self.assertRule(11)

    def test_rule11_external_reference_is_not_checked_as_permalink(self):
        ref = {"kind": "external", "url": "https://example.com/docs", "reading": "full"}
        self.set_field(REV1, "references", [ref])
        self.assertEqual(self.errors(), [])

    def test_rule12_outcome_judged_without_judge(self):
        self.set_field(POSTING, "outcome", "aligned")
        self.assertRule(12)

    def test_rule12_judge_filled_while_pending(self):
        self.set_field(POSTING, "outcome_judged_by", "example-reviewer")
        self.assertRule(12)

    def test_rule12_judged_outcome_with_judge_is_valid(self):
        self.set_field(POSTING, "outcome", "disagreed")
        self.set_field(POSTING, "outcome_judged_by", "example-reviewer")
        self.assertEqual(self.errors(), [])


if __name__ == "__main__":
    unittest.main()
