#!/usr/bin/env python3
"""pr-review の記録（DIR/pulls/ 以下の .md）が records.md の「検査」1〜12 を満たすか確かめる。"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SUPPORTED_TYPES = ("pull", "snapshot", "finding", "assessment", "draft", "revision", "posting")

SHA40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
ORDINARY_ID = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{6}")
PULL_ID = re.compile(r"[^/#@\s]+/[^/#@\s]+#\d+")
SNAPSHOT_ID = re.compile(r"[^/#@\s]+/[^/#@\s]+#\d+@[0-9a-f]{7}")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})")
PERMALINK = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/blob/[0-9a-f]{40}/[^\s#]+(#L\d+(C\d+)?(-L\d+(C\d+)?)?)?")
FRONT_MATTER_LINE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*): (.*)")
REV_FILE = re.compile(r"rev-(\d{3})\.md")


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def string(value):
    return None if isinstance(value, str) else "文字列ではありません"


def integer(value):
    return None if is_int(value) else "整数ではありません"


def boolean(value):
    return None if isinstance(value, bool) else "真偽値ではありません"


def null_only(value):
    return None if value is None else "段階 1 では null でなければなりません"


def nullable(check):
    return lambda value: None if value is None else check(value)


def pattern(regex, description):
    def check(value):
        if not isinstance(value, str):
            return "文字列ではありません"
        return None if regex.fullmatch(value) else f"{description}の形ではありません"

    return check


def enum(*allowed):
    def check(value):
        if isinstance(value, str) and value in allowed:
            return None
        return "次のどれかでなければなりません: " + ", ".join(allowed)

    return check


ordinary_id = pattern(ORDINARY_ID, "通常の id（yyyymmddThhmmssZ-16 進 6 桁）")
pull_id = pattern(PULL_ID, "PR の id（owner/repo#番号）")
snapshot_id = pattern(SNAPSHOT_ID, "スナップショットの id（owner/repo#番号@head7）")
sha40 = pattern(SHA40, "40 桁の 16 進")
sha256 = pattern(SHA256, "SHA-256（16 進 64 桁）")
timestamp = pattern(TIMESTAMP, "UTC 時刻（ISO 8601）")


def positive_int(value):
    if not is_int(value):
        return "整数ではありません"
    return None if value >= 1 else "1 以上でなければなりません"


def location(value):
    if not isinstance(value, dict):
        return "オブジェクトではありません"
    keys = {"path", "start_line", "end_line", "side"}
    if set(value) != keys:
        return "項目が path, start_line, end_line, side の 4 つではありません"
    for name, check in (("path", string), ("start_line", integer), ("end_line", integer),
                        ("side", enum("left", "right"))):
        problem = check(value[name])
        if problem:
            return f"{name}: {problem}"
    return None


def references(value):
    if not isinstance(value, list):
        return "配列ではありません"
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            return f"[{index}]: オブジェクトではありません"
        kind = item.get("kind")
        if kind == "repo":
            expected = {"kind", "url"}
        elif kind == "external":
            expected = {"kind", "url", "reading"}
        else:
            return f"[{index}]: kind は repo か external でなければなりません"
        if set(item) != expected:
            return f"[{index}]: kind が {kind} の項目は {', '.join(sorted(expected))} でなければなりません"
        problem = string(item["url"])
        if not problem and kind == "external":
            problem = enum("full", "summary", "unverified")(item["reading"])
        if problem:
            return f"[{index}]: {problem}"
    return None


def string_list(value):
    if not isinstance(value, list):
        return "配列ではありません"
    return None if all(isinstance(item, str) for item in value) else "文字列だけの配列ではありません"


SPECS = {
    "pull": {
        "id": pull_id, "url": string, "series": nullable(string), "title": nullable(string),
        "author": nullable(string), "fetched_at": timestamp,
    },
    "snapshot": {
        "id": snapshot_id, "pull_id": pull_id, "head_sha": sha40, "base_sha": nullable(sha40),
        "fetched_at": timestamp,
    },
    "finding": {
        "id": ordinary_id, "pull_id": pull_id, "snapshot_id": snapshot_id, "run_id": null_only,
        "origin": enum("human", "detector"), "origin_ref": nullable(string), "title": string,
        "body_hash": sha256, "location": nullable(location),
        "confidence": enum("confirmed", "plausible", "unknown"), "theme_key": nullable(string),
        "norm_gap": nullable(enum("missing", "unclear", "violated", "conflicting")),
        "norm_ref": nullable(string), "dismissed_reason": nullable(string), "created_by": string,
        "created_at": timestamp,
    },
    "assessment": {
        "id": ordinary_id, "finding_id": ordinary_id, "profile_id": null_only,
        "action": enum("share", "ask", "analyze", "change"), "blocking": boolean,
        "importance": enum("high", "mid", "low"), "intent_quote": string,
        "premise_quote": nullable(string), "rationale_ref": nullable(string), "assessed_by": string,
        "assessed_at": timestamp,
    },
    "draft": {
        "id": ordinary_id, "assessment_id": ordinary_id, "withdrawn_at": nullable(timestamp),
    },
    "revision": {
        "draft_id": ordinary_id, "rev": positive_int, "references": references, "changed_by": string,
        "changed_at": timestamp, "reason_quote": nullable(string), "approved_by": nullable(string),
        "approved_at": nullable(timestamp),
    },
    "posting": {
        "id": ordinary_id, "draft_id": ordinary_id, "rev": positive_int, "mode": enum("new", "edit"),
        "github_comment_id": string, "url": string, "payload_hash": sha256, "anchor_verified": boolean,
        "head_sha_at_post": sha40, "posted_at": timestamp,
        "outcome": enum("pending", "aligned", "changed", "disagreed", "dropped"),
        "reply_refs": string_list, "outcome_judged_by": nullable(string),
    },
}


class Record:
    def __init__(self, path, kind, front_matter, body, place):
        self.path = path
        self.kind = kind
        self.fm = front_matter
        self.body = body
        self.place = place

    def text(self, key):
        value = self.fm.get(key)
        return value if isinstance(value, str) else None


def parse_front_matter(content):
    lines = content.split("\n")
    if lines[0].rstrip("\r") != "---":
        raise ValueError("先頭が --- の行ではありません（front matter がありません）")
    front = {}
    for number, raw in enumerate(lines[1:], start=2):
        line = raw.rstrip("\r")
        if line == "---":
            return front, "\n".join(lines[number:])
        match = FRONT_MATTER_LINE.fullmatch(line)
        if not match:
            raise ValueError(f"{number} 行目が「キー: JSON の値」として読めません: {line}")
        key, text = match.groups()
        if key in front:
            raise ValueError(f"{number} 行目のキー {key} が重複しています")
        try:
            front[key] = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"{number} 行目の {key} の値が JSON として読めません: {error.msg}") from error
    raise ValueError("front matter を閉じる --- の行がありません")


def classify(parts):
    """pulls/ からの相対パスの各部分から、置き場所の種類と、そこから決まる値を返す。"""
    if len(parts) < 4:
        return None
    owner, repo, number, *rest = parts
    if not number.isdigit():
        return None
    place = {"pull_id": f"{owner}/{repo}#{number}"}
    name = rest[-1]
    if rest == ["pull.md"]:
        return "pull", place
    if len(rest) == 2 and rest[0] == "snapshots":
        place["head7"] = name[:-3]
        return "snapshot", place
    if len(rest) < 3 or rest[0] != "findings":
        return None
    place["finding_id"] = rest[1]
    tail = rest[2:]
    if tail == ["finding.md"]:
        return "finding", place
    if len(tail) == 2 and tail[0] == "assessments":
        place["id"] = name[:-3]
        return "assessment", place
    if len(tail) >= 3 and tail[0] == "drafts":
        place["draft_id"] = tail[1]
        if tail[2:] == ["draft.md"]:
            return "draft", place
        if len(tail) == 3 and REV_FILE.fullmatch(name):
            place["rev_file"] = int(REV_FILE.fullmatch(name).group(1))
            return "revision", place
        if len(tail) == 4 and tail[2] == "postings":
            place["id"] = name[:-3]
            return "posting", place
    return None


class Validator:
    def __init__(self):
        self.errors = []

    def add(self, path, rule, message):
        self.errors.append({"path": path, "rule": rule, "message": message})

    def check_fields(self, rec):
        spec = SPECS[rec.kind]
        fm = rec.fm
        if "schema" not in fm:
            self.add(rec.path, 1, "必須項目 schema がありません")
        elif fm["schema"] != 1 or not is_int(fm["schema"]):
            self.add(rec.path, 1, "schema: 今の版は 1 です")
        for key, check in spec.items():
            if key not in fm:
                self.add(rec.path, 1, f"必須項目 {key} がありません")
                continue
            message = check(fm[key])
            if message:
                self.add(rec.path, 1, f"{key}: {message}")
        for key in fm:
            if key not in spec and key not in ("type", "schema"):
                self.add(rec.path, 1, f"未知の項目 {key} があります")

    def check_place(self, rec):
        place = rec.place

        def expect(key, expected, label):
            actual = rec.text(key)
            if actual is not None and actual != expected:
                self.add(rec.path, 3, f"{key}（{actual}）が{label}（{expected}）と一致しません")

        if rec.kind == "pull":
            expect("id", place["pull_id"], "フォルダから決まる PR の id")
        elif rec.kind == "snapshot":
            expect("pull_id", place["pull_id"], "フォルダから決まる PR の id")
            head = rec.text("head_sha")
            if head is not None and head[:7] != place["head7"]:
                self.add(rec.path, 3, f"ファイル名（{place['head7']}）が head_sha の先頭 7 文字（{head[:7]}）と一致しません")
            expect("id", f"{place['pull_id']}@{place['head7']}", "ファイル名から決まるスナップショットの id")
        elif rec.kind == "finding":
            expect("id", place["finding_id"], "フォルダ名")
            expect("pull_id", place["pull_id"], "フォルダから決まる PR の id")
        elif rec.kind == "assessment":
            expect("id", place["id"], "ファイル名")
            expect("finding_id", place["finding_id"], "親のフォルダの finding の id")
        elif rec.kind == "draft":
            expect("id", place["draft_id"], "フォルダ名")
        elif rec.kind == "revision":
            expect("draft_id", place["draft_id"], "フォルダ名")
        elif rec.kind == "posting":
            expect("id", place["id"], "ファイル名")
            expect("draft_id", place["draft_id"], "フォルダ名")

    def check_content(self, rec):
        fm = rec.fm
        if rec.kind == "finding":
            digest = hashlib.sha256(rec.body.strip("\n").encode("utf-8")).hexdigest()
            if rec.text("body_hash") is not None and fm["body_hash"] != digest:
                self.add(rec.path, 5, f"body_hash が本文の SHA-256 と一致しません（本文の値は {digest}）")
            loc = fm.get("location")
            if isinstance(loc, dict) and is_int(loc.get("start_line")) and is_int(loc.get("end_line")):
                if loc["start_line"] < 1:
                    self.add(rec.path, 10, "location.start_line が 1 未満です")
                if loc["start_line"] > loc["end_line"]:
                    self.add(rec.path, 10, "location.start_line が end_line より大きいです")
        elif rec.kind == "revision":
            rev = fm.get("rev")
            if is_int(rev) and rev != rec.place["rev_file"]:
                self.add(rec.path, 6, f"rev（{rev}）がファイル名の番号（{rec.place['rev_file']}）と一致しません")
            if (fm.get("approved_by") is None) != (fm.get("approved_at") is None):
                self.add(rec.path, 7, "approved_by と approved_at は、両方埋めるか両方 null にします")
            if rev == 1 and fm.get("reason_quote") is not None:
                self.add(rec.path, 1, "reason_quote: 第 1 版は null でなければなりません")
            refs = fm.get("references")
            if isinstance(refs, list):
                for index, ref in enumerate(refs):
                    if isinstance(ref, dict) and ref.get("kind") == "repo" and isinstance(ref.get("url"), str):
                        if not PERMALINK.fullmatch(ref["url"]):
                            self.add(rec.path, 11, f"references[{index}].url が、40 桁の SHA に固定された blob の固定リンクではありません: {ref['url']}")
        elif rec.kind == "posting":
            outcome = fm.get("outcome")
            judged_by = fm.get("outcome_judged_by")
            if isinstance(outcome, str) and outcome != "pending" and judged_by is None:
                self.add(rec.path, 12, f"outcome が {outcome} なのに outcome_judged_by が埋まっていません")
            if outcome == "pending" and judged_by is not None:
                self.add(rec.path, 12, "outcome が pending のときは outcome_judged_by を埋めません")

    def check_references_across(self, records):
        by_kind = {kind: [r for r in records if r.kind == kind] for kind in SUPPORTED_TYPES}
        pulls = {r.text("id") for r in by_kind["pull"]}
        snapshots = {r.text("id"): r for r in by_kind["snapshot"]}
        findings = {r.text("id") for r in by_kind["finding"]}
        assessments = {r.text("id"): r for r in by_kind["assessment"]}
        drafts = {r.text("id") for r in by_kind["draft"]}

        for rec in by_kind["snapshot"]:
            self.require(rec, "pull_id", pulls, "PR")
        for rec in by_kind["finding"]:
            self.require(rec, "pull_id", pulls, "PR")
            snap_id = rec.text("snapshot_id")
            if snap_id is None:
                continue
            snap = snapshots.get(snap_id)
            if snap is None:
                self.add(rec.path, 4, f"snapshot_id が指すスナップショット（{snap_id}）がありません")
            elif snap.text("pull_id") != rec.text("pull_id"):
                self.add(rec.path, 4, f"snapshot_id が指すスナップショット（{snap_id}）が、別の PR のものです")
        for rec in by_kind["assessment"]:
            self.require(rec, "finding_id", findings, "finding")
        for rec in by_kind["draft"]:
            target = rec.text("assessment_id")
            if target is None:
                continue
            assessment = assessments.get(target)
            if assessment is None:
                self.add(rec.path, 4, f"assessment_id が指す assessment（{target}）がありません")
            elif assessment.text("finding_id") != rec.place["finding_id"]:
                self.add(rec.path, 4, f"assessment_id が指す assessment（{target}）が、この finding のものではありません")
        for kind in ("revision", "posting"):
            for rec in by_kind[kind]:
                self.require(rec, "draft_id", drafts, "draft")

    def require(self, rec, key, existing, label):
        value = rec.text(key)
        if value is not None and value not in existing:
            self.add(rec.path, 4, f"{key} が指す {label}（{value}）がありません")

    def check_revisions_across(self, records):
        folders = {}
        for rec in records:
            if rec.kind == "revision":
                folders.setdefault(str(Path(rec.path).parent), []).append(rec)
        for folder, recs in sorted(folders.items()):
            numbers = {r.place["rev_file"] for r in recs}
            for number in range(1, max(numbers) + 1):
                if number not in numbers:
                    self.add(folder, 6, f"rev-{number:03d}.md がありません（rev は 1 から連続させます）")

    def check_postings_across(self, records):
        revisions = {}
        for rec in records:
            if rec.kind == "revision" and rec.text("draft_id") is not None and is_int(rec.fm.get("rev")):
                revisions[(rec.fm["draft_id"], rec.fm["rev"])] = rec
        seen = {}
        for rec in records:
            if rec.kind != "posting":
                continue
            draft, rev, mode = rec.text("draft_id"), rec.fm.get("rev"), rec.text("mode")
            if draft is None or not is_int(rev):
                continue
            revision = revisions.get((draft, rev))
            if revision is None:
                self.add(rec.path, 8, f"rev {rev} の版がありません")
            elif revision.fm.get("approved_by") is None or revision.fm.get("approved_at") is None:
                self.add(rec.path, 8, f"rev {rev} の版は承認されていません")
            if mode is None:
                continue
            key = (draft, rev, mode)
            if key in seen:
                self.add(rec.path, 9, f"同じ（draft, rev, mode）の posting が {seen[key]} にもあります")
            else:
                seen[key] = rec.path

    def run(self, store):
        root = store / "pulls"
        records = []
        files = sorted(root.rglob("*.md"))
        for file in files:
            rel = file.relative_to(root)
            shown = rel.as_posix()
            try:
                content = file.read_text(encoding="utf-8")
                front, body = parse_front_matter(content)
            except UnicodeDecodeError:
                self.add(shown, 1, "UTF-8 として読めません")
                continue
            except ValueError as error:
                self.add(shown, 1, str(error))
                continue
            kind = front.get("type")
            if not isinstance(kind, str):
                self.add(shown, 1, "必須項目 type が文字列ではありません" if "type" in front else "必須項目 type がありません")
                continue
            if kind not in SUPPORTED_TYPES:
                self.add(shown, 2, f"未対応の種類です: {kind}")
                continue
            found = classify(rel.parts)
            if found is None:
                self.add(shown, 3, "記録の置き場所として想定していない位置です")
                place = None
            elif found[0] != kind:
                self.add(shown, 3, f"type（{kind}）がこの位置の種類（{found[0]}）と一致しません")
                place = None
            else:
                place = found[1]
            rec = Record(shown, kind, front, body, place)
            self.check_fields(rec)
            if place is not None:
                self.check_place(rec)
                self.check_content(rec)
                records.append(rec)
        self.check_references_across(records)
        self.check_revisions_across(records)
        self.check_postings_across(records)
        self.errors.sort(key=lambda e: (e["path"], e["rule"]))
        return len(files)


def main():
    parser = argparse.ArgumentParser(description="pr-review の記録を検査する")
    parser.add_argument("--store", required=True, metavar="DIR", help="記録の置き場所の根")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    store = Path(args.store)
    if not (store / "pulls").is_dir():
        print(f"{store / 'pulls'} がありません", file=sys.stderr)
        return 2

    validator = Validator()
    checked = validator.run(store)
    if args.format == "json":
        print(json.dumps({"errors": validator.errors, "checked": checked}, ensure_ascii=False, indent=2))
    else:
        for error in validator.errors:
            print(f"{error['path']}: [{error['rule']}] {error['message']}")
        if validator.errors:
            print(f"エラー {len(validator.errors)} 件（検査したファイル {checked} 件）")
        else:
            print(f"エラーなし（検査したファイル {checked} 件）")
    return 1 if validator.errors else 0


if __name__ == "__main__":
    sys.exit(main())
